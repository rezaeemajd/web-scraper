import hashlib
import ipaddress
import socket
import urllib.robotparser
import json
import time
from urllib.parse import urljoin, urlsplit

import httpx
from django.core.cache import cache

from datahub.models import RawCapture
from .models import Source


class FetchBlocked(Exception):
    pass


class FetchTransient(Exception):
    pass


_MAX_REDIRECTS = 5
_ROBOTS_CACHE_TTL = 10 * 60


def _same_domain(source: Source, url: str) -> bool:
    return (urlsplit(source.base_url).hostname or "").lower() == (
        urlsplit(url).hostname or ""
    ).lower()


def _assert_public_url(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise FetchBlocked("url must use http or https")

    try:
        literal = ipaddress.ip_address(parsed.hostname)
    except ValueError:
        literal = None

    if literal is not None:
        addresses = [literal]
    else:
        try:
            addresses = {
                ipaddress.ip_address(info[4][0])
                for info in socket.getaddrinfo(
                    parsed.hostname,
                    parsed.port or (443 if parsed.scheme == "https" else 80),
                    type=socket.SOCK_STREAM,
                )
            }
        except (OSError, ValueError):
            raise FetchBlocked("host could not be resolved")

    if not addresses or any(not address.is_global for address in addresses):
        raise FetchBlocked("host resolves to a non-public address")


def _bounded_response_text(response, max_bytes: int) -> str:
    chunks = []
    total = 0
    for chunk in response.iter_bytes():
        if not chunk:
            continue
        remaining = max_bytes - total
        if remaining <= 0:
            break
        piece = chunk[:remaining]
        chunks.append(piece)
        total += len(piece)
        if total >= max_bytes:
            break
    body = b"".join(chunks)
    return body.decode(response.encoding or "utf-8", errors="replace")


def _rate_limit(source: Source) -> None:
    """Atomic fixed-window source limiter.

    The first request in a window is claimed with cache.add(1); later requests
    use INCR. This works with Redis and avoids requiring a non-atomic
    get-then-set sequence.
    """
    limit = max(1, source.rate_limit_per_minute)
    window = int(time.time() // 60)
    key = f"cdi:source-rate:{source.pk}:{window}"
    if cache.add(key, 1, timeout=61):
        return
    count = cache.incr(key)
    if count > limit:
        raise FetchBlocked("source rate limit exceeded")


def _capture_robots(source: Source, robots_url: str):
    rp = urllib.robotparser.RobotFileParser()
    cache_key = f"cdi:robots:{source.pk}:{hashlib.sha256(source.user_agent.encode()).hexdigest()}"
    cached = cache.get(cache_key)
    if cached is not None:
        try:
            rp.parse(json.loads(cached))
            return rp
        except (TypeError, ValueError):
            cache.delete(cache_key)
    try:
        _assert_public_url(robots_url)
        with httpx.Client(
            timeout=httpx.Timeout(5.0, connect=3.0),
            follow_redirects=False,
            trust_env=False,
            headers={"User-Agent": source.user_agent},
        ) as robots_client:
            with robots_client.stream("GET", robots_url) as rr:
                if rr.is_success and _same_domain(source, str(rr.url)):
                    robots_text = _bounded_response_text(
                        rr, min(source.max_response_bytes, 256 * 1024)
                    )
                    lines = robots_text.splitlines()
                    rp.parse(lines)
                    cache.set(
                        cache_key,
                        json.dumps(lines, ensure_ascii=False),
                        _ROBOTS_CACHE_TTL,
                    )
    except Exception:
        pass
    return rp


def _request_with_safe_redirects(source: Source, url: str, client=None):
    current_url = url
    redirected = False
    owns_client = client is None
    if owns_client:
        client = httpx.Client(
            timeout=httpx.Timeout(20.0, connect=10.0),
            follow_redirects=False,
            trust_env=False,
            headers={"User-Agent": source.user_agent},
        )
    try:
        for _ in range(_MAX_REDIRECTS + 1):
            if not _same_domain(source, current_url):
                raise FetchBlocked(
                    "redirected outside source domain"
                    if redirected
                    else "url is outside source domain"
                )
            _assert_public_url(current_url)

            with client.stream("GET", current_url) as response:
                if response.status_code not in {301, 302, 303, 307, 308}:
                    chunks = []
                    total = 0
                    for chunk in response.iter_bytes():
                        if not chunk:
                            continue
                        remaining = source.max_response_bytes - total
                        if remaining <= 0:
                            break
                        piece = chunk[:remaining]
                        chunks.append(piece)
                        total += len(piece)
                        if total >= source.max_response_bytes:
                            break
                    body = b"".join(chunks)
                    buffered = httpx.Response(
                        response.status_code,
                        headers=response.headers,
                        content=body,
                        request=getattr(response, "request", None),
                    )
                    return buffered, current_url

                location = response.headers.get("location")
                if not location:
                    return httpx.Response(
                        response.status_code,
                        headers=response.headers,
                        content=b"",
                        request=getattr(response, "request", None),
                    ), current_url
                current_url = urljoin(current_url, location)
                redirected = True

        raise FetchBlocked("too many redirects")
    finally:
        if owns_client:
            client.close()


def capture_url(source: Source, url: str, *, client=None) -> RawCapture:
    if not source.allowed or source.status != Source.Status.ACTIVE:
        raise FetchBlocked("source is not active")
    if not _same_domain(source, url):
        raise FetchBlocked("url is outside source domain")
    _assert_public_url(url)

    if source.respect_robots:
        base = urlsplit(source.base_url)
        robots_url = f"{base.scheme}://{base.netloc}/robots.txt"
        rp = _capture_robots(source, robots_url)
        if rp.default_entry is not None and not rp.can_fetch(source.user_agent, url):
            return RawCapture.objects.create(
                url=url,
                status=RawCapture.Status.BLOCKED,
                error_message="robots.txt disallowed",
            )

    try:
        _rate_limit(source)
        response, final_url = _request_with_safe_redirects(source, url, client=client)
        try:
            body = response.content
            text = body.decode(response.encoding or "utf-8", errors="replace")
            return RawCapture.objects.create(
                url=url,
                status_code=response.status_code,
                content_type=response.headers.get("content-type", ""),
                body=text,
                headers=dict(response.headers),
                body_sha256=hashlib.sha256(body).hexdigest(),
                status=RawCapture.Status.SUCCESS
                if response.is_success
                else RawCapture.Status.ERROR,
                error_message=(
                    f"transient:http_status:{response.status_code}"
                    if response.status_code in {408, 429} or response.status_code >= 500
                    else ""
                ),
            )
        finally:
            response.close()
    except FetchBlocked as exc:
        return RawCapture.objects.create(
            url=url,
            status=RawCapture.Status.BLOCKED,
            error_message=str(exc)[:2000],
        )
    except (httpx.TimeoutException, httpx.NetworkError) as exc:
        return RawCapture.objects.create(
            url=url,
            status=RawCapture.Status.ERROR,
            error_message=f"transient:{type(exc).__name__}:{str(exc)[:1900]}",
        )
    except Exception as exc:
        return RawCapture.objects.create(
            url=url,
            status=RawCapture.Status.ERROR,
            error_message=str(exc)[:2000],
        )
