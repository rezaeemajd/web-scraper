import hashlib
import socket

import pytest

from datahub.models import RawCapture
from . import fetcher
from .fetcher import _same_domain
from .models import Source


def test_same_domain_rejects_external_host():
    source = type("SourceStub", (), {"base_url": "https://example.com"})()
    assert _same_domain(source, "https://example.com/path")
    assert not _same_domain(source, "https://evil.example/path")


class _FakeResponse:
    def __init__(self, url, body=b"hello", status_code=200, content_type="text/html"):
        self.url = url
        self.status_code = status_code
        self.headers = {"content-type": content_type}
        self.encoding = "utf-8"
        self.is_success = 200 <= status_code < 300
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def close(self):
        return None

    def iter_bytes(self):
        yield self._body


class _FakeClient:
    responses = []
    init_kwargs = []

    def __init__(self, *args, **kwargs):
        type(self).init_kwargs.append(kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, url):
        return type(self).responses.pop(0)

    def stream(self, method, url):
        return type(self).responses.pop(0)


@pytest.mark.django_db
def test_capture_url_persists_sha256_and_respects_response_limit(monkeypatch):
    source = Source.objects.create(
        name="Limited Source",
        domain="example.com",
        base_url="https://example.com",
        respect_robots=False,
        max_response_bytes=5,
    )
    _FakeClient.responses = [_FakeResponse(source.base_url + "/page", body=b"abcdefghij")]
    _FakeClient.init_kwargs = []
    monkeypatch.setattr(fetcher.httpx, "Client", _FakeClient)
    monkeypatch.setattr(fetcher, "_assert_public_url", lambda url: None)
    monkeypatch.setattr(fetcher.cache, "add", lambda *args, **kwargs: True)

    capture = fetcher.capture_url(source, "https://example.com/page")

    assert capture.status == RawCapture.Status.SUCCESS
    assert capture.body == "abcde"
    assert capture.body_sha256 == hashlib.sha256(b"abcde").hexdigest()


@pytest.mark.django_db
def test_capture_url_blocks_external_redirect(monkeypatch):
    source = Source.objects.create(
        name="Redirect Source",
        domain="example.com",
        base_url="https://example.com",
        respect_robots=False,
    )
    _FakeClient.responses = [_FakeResponse("https://example.com/page", body=b"", status_code=302)]
    _FakeClient.responses[0].headers["location"] = "https://evil.example/landing"
    _FakeClient.init_kwargs = []
    monkeypatch.setattr(fetcher.httpx, "Client", _FakeClient)
    monkeypatch.setattr(fetcher.cache, "add", lambda *args, **kwargs: True)

    capture = fetcher.capture_url(source, "https://example.com/page")

    assert capture.status == RawCapture.Status.BLOCKED
    assert capture.error_message == "redirected outside source domain"


@pytest.mark.django_db
def test_capture_url_does_not_follow_external_robots_redirect(monkeypatch):
    source = Source.objects.create(
        name="Robots Redirect Source",
        domain="example.com",
        base_url="https://example.com",
        respect_robots=True,
    )
    _FakeClient.responses = [
        _FakeResponse(
            "https://evil.example/robots.txt",
            body=b"User-agent: *\nDisallow: /page\n",
        ),
        _FakeResponse(
            "https://example.com/page",
            body=b"<html>allowed</html>",
        ),
    ]
    _FakeClient.init_kwargs = []
    monkeypatch.setattr(fetcher.httpx, "Client", _FakeClient)
    monkeypatch.setattr(fetcher.cache, "add", lambda *args, **kwargs: True)

    capture = fetcher.capture_url(source, "https://example.com/page")

    assert capture.status == RawCapture.Status.SUCCESS
    assert capture.body == "<html>allowed</html>"
    assert _FakeClient.init_kwargs[0]["follow_redirects"] is False
    assert _FakeClient.init_kwargs[1]["follow_redirects"] is False


@pytest.mark.django_db
def test_capture_url_enforces_source_rate_limit(monkeypatch):
    source = Source.objects.create(
        name="Rate Limited Source",
        domain="example.com",
        base_url="https://example.com",
        respect_robots=False,
        rate_limit_per_minute=60,
    )
    _FakeClient.responses = [_FakeResponse("https://example.com/page", body=b"ok")]
    _FakeClient.init_kwargs = []
    monkeypatch.setattr(fetcher.httpx, "Client", _FakeClient)
    monkeypatch.setattr(fetcher.cache, "add", lambda *args, **kwargs: False)

    capture = fetcher.capture_url(source, "https://example.com/page")

    assert capture.status == RawCapture.Status.BLOCKED
    assert capture.error_message == "source rate limit exceeded"
    assert len(_FakeClient.responses) == 1


def test_assert_public_url_blocks_private_and_accepts_public(monkeypatch):
    from .fetcher import _assert_public_url, FetchBlocked

    with pytest.raises(FetchBlocked, match="non-public"):
        _assert_public_url("http://127.0.0.1:8000/")

    monkeypatch.setattr(
        fetcher.socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 80))
        ],
    )
    _assert_public_url("https://example.com/")


@pytest.mark.django_db
def test_capture_url_blocks_private_redirect(monkeypatch):
    source = Source.objects.create(
        name="Private Redirect Source",
        domain="example.com",
        base_url="https://example.com",
        respect_robots=False,
    )
    _FakeClient.responses = [_FakeResponse(
        "https://example.com/page",
        body=b"",
        status_code=302,
    )]
    _FakeClient.responses[0].headers["location"] = "http://127.0.0.1:8000/admin/"
    _FakeClient.init_kwargs = []
    monkeypatch.setattr(fetcher.httpx, "Client", _FakeClient)
    monkeypatch.setattr(fetcher.cache, "add", lambda *args, **kwargs: True)
    monkeypatch.setattr(fetcher, "_assert_public_url", lambda url: (
        (_ for _ in ()).throw(fetcher.FetchBlocked("host resolves to a non-public address"))
        if "127.0.0.1" in url else None
    ))

    capture = fetcher.capture_url(source, "https://example.com/page")

    assert capture.status == RawCapture.Status.BLOCKED
    assert "non-public" in capture.error_message


@pytest.mark.django_db
@pytest.mark.parametrize("status_code", [408, 429, 500, 502, 503, 504])
def test_capture_url_marks_retryable_http_status_transient(monkeypatch, status_code):
    source = Source.objects.create(
        name=f"Transient {status_code}",
        domain="example.com",
        base_url="https://example.com",
        respect_robots=False,
    )
    _FakeClient.responses = [
        _FakeResponse(
            source.base_url + "/temporary",
            body=b"temporary",
            status_code=status_code,
        )
    ]
    _FakeClient.init_kwargs = []
    monkeypatch.setattr(fetcher.httpx, "Client", _FakeClient)
    monkeypatch.setattr(fetcher.cache, "add", lambda *args, **kwargs: True)

    capture = fetcher.capture_url(source, "https://example.com/temporary")

    assert capture.status == RawCapture.Status.ERROR
    assert capture.error_message == f"transient:http_status:{status_code}"
