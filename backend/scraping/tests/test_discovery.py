from types import SimpleNamespace

from scraping.discovery import (
    bounded_discovery,
    canonicalize_url,
    extract_same_domain_links,
)


def test_canonicalize_removes_fragment():
    assert canonicalize_url("https://example.com/a#section") == "https://example.com/a"


def test_extract_same_domain_links_filters_external_and_fragments():
    html = """
    <a href="/medicine/1#x">one</a>
    <a href="https://example.com/pharmacy/2">two</a>
    <a href="https://other.example/x">external</a>
    <a href="mailto:test@example.com">mail</a>
    """
    links = extract_same_domain_links(
        html,
        "https://example.com/",
        "example.com",
    )
    assert links == [
        "https://example.com/medicine/1",
        "https://example.com/pharmacy/2",
    ]


def test_bounded_discovery_is_breadth_first_and_capped():
    captures = {
        "https://example.com/": SimpleNamespace(
            status="success",
            body='<a href="/a">a</a><a href="/b">b</a>',
        ),
        "https://example.com/a": SimpleNamespace(
            status="success",
            body='<a href="/c">c</a>',
        ),
        "https://example.com/b": SimpleNamespace(
            status="success",
            body='<a href="/d">d</a>',
        ),
    }

    class Source:
        base_url = "https://example.com"

    pages = bounded_discovery(
        Source(),
        ["https://example.com/"],
        captures.__getitem__,
        max_pages=3,
        max_urls=10,
    )

    assert [url for url, _capture in pages] == [
        "https://example.com/",
        "https://example.com/a",
        "https://example.com/b",
    ]
