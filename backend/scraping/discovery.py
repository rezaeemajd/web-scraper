"""Bounded, same-domain HTML link discovery for CDI source crawls."""

from collections import deque
from urllib.parse import urldefrag, urljoin, urlparse


def _host(url):
    return (urlparse(url).hostname or "").lower().rstrip(".")


def canonicalize_url(url):
    """Remove fragments without changing query/path semantics."""
    clean, _fragment = urldefrag(url.strip())
    parsed = urlparse(clean)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return clean


def extract_same_domain_links(html, current_url, allowed_host):
    """Return deterministic same-host HTTP(S) links from one HTML document."""
    from selectolax.lexbor import LexborHTMLParser

    tree = LexborHTMLParser(html)
    links = set()
    for node in tree.css("a[href]"):
        href = node.attributes.get("href")
        if not href:
            continue
        candidate = canonicalize_url(urljoin(current_url, href))
        if not candidate:
            continue
        if _host(candidate) != allowed_host:
            continue
        links.add(candidate)
    return sorted(links)


def bounded_discovery(
    source,
    seeds,
    fetch_page,
    *,
    max_pages=10,
    max_urls=100,
    is_success=lambda capture: getattr(capture, "status", None) == "success",
):
    """Breadth-first same-domain discovery with hard page/URL limits."""
    allowed_host = _host(source.base_url)
    queue = deque()
    queued = set()

    for seed in seeds:
        url = canonicalize_url(seed)
        if url and _host(url) == allowed_host and url not in queued:
            queued.add(url)
            queue.append(url)

    visited = set()
    pages = []

    while queue and len(visited) < max_pages and len(visited) < max_urls:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        capture = fetch_page(url)
        pages.append((url, capture))
        if not is_success(capture):
            continue

        for link in extract_same_domain_links(capture.body, url, allowed_host):
            if link not in queued and len(queued) < max_urls:
                queued.add(link)
                queue.append(link)

    return pages
