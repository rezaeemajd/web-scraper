import hashlib
import urllib.robotparser
from urllib.parse import urlsplit

import httpx

from .models import Source
from datahub.models import RawCapture


class FetchBlocked(Exception):
    pass


def _same_domain(source: Source, url: str) -> bool:
    return (urlsplit(source.base_url).hostname or "").lower() == (
        urlsplit(url).hostname or ""
    ).lower()


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


def capture_url(source: Source, url: str) -> RawCapture:
    if not source.allowed or source.status != Source.Status.ACTIVE:
        raise FetchBlocked("source is not active")
    if not _same_domain(source, url):
        raise FetchBlocked("url is outside source domain")

    if source.respect_robots:
        rp = urllib.robotparser.RobotFileParser()
        base = urlsplit(source.base_url)
        robots_url = f"{base.scheme}://{base.netloc}/robots.txt"
        try:
            with httpx.Client(
                timeout=httpx.Timeout(5.0, connect=3.0),
                follow_redirects=True,
                headers={"User-Agent": source.user_agent},
            ) as robots_client:
                with robots_client.stream("GET", robots_url) as rr:
                    if rr.is_success:
                        robots_text = _bounded_response_text(rr, min(source.max_response_bytes, 256 * 1024))
                        rp.parse(robots_text.splitlines())
        except Exception:
            pass

        if rp.default_entry is not None and not rp.can_fetch(source.user_agent, url):
            return RawCapture.objects.create(
                url=url,
                status=RawCapture.Status.BLOCKED,
                error_message="robots.txt disallowed",
            )

    try:
        with httpx.Client(
            timeout=httpx.Timeout(20.0, connect=10.0),
            follow_redirects=True,
            headers={"User-Agent": source.user_agent},
        ) as client:
            with client.stream("GET", url) as response:
                final_url = str(response.url)
                if not _same_domain(source, final_url):
                    return RawCapture.objects.create(
                        url=url,
                        status_code=response.status_code,
                        content_type=response.headers.get("content-type", ""),
                        headers=dict(response.headers),
                        status=RawCapture.Status.BLOCKED,
                        error_message="redirected outside source domain",
                    )

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

        text = body.decode(response.encoding or "utf-8", errors="replace")
        return RawCapture.objects.create(
            url=url,
            status_code=response.status_code,
            content_type=response.headers.get("content-type", ""),
            body=text,
            headers=dict(response.headers),
            body_sha256=hashlib.sha256(body).hexdigest(),
            status=RawCapture.Status.SUCCESS if response.is_success else RawCapture.Status.ERROR,
        )
    except Exception as exc:
        return RawCapture.objects.create(
            url=url,
            status=RawCapture.Status.ERROR,
            error_message=str(exc)[:2000],
        )
