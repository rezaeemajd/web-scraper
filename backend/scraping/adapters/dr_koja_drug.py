"""Source-specific parser for Dr-Koja public drug index pages.

Dr-Koja's public index exposes medicine detail links under /drug/.  The parser
uses those stable semantic links rather than assuming Pillix table markup.
It extracts only information actually present on the index card and keeps the
detail URL as provenance for the next crawl stage.
"""

import re
from urllib.parse import urljoin

from selectolax.lexbor import LexborHTMLParser

from datahub.pipeline import normalize_text


_DRUG_HREF = re.compile(r"^/drug/[^?#]+", re.IGNORECASE)
_LATIN_RE = re.compile(r"[A-Za-z]")


def _clean(value):
    return normalize_text(value or "").strip()


def _latin_line(text):
    for part in re.split(r"[\n|•]+", text):
        value = _clean(part)
        if value and _LATIN_RE.search(value):
            return value
    return ""


def extract_drugs(html, source_url):
    """Extract real drug index cards from a Dr-Koja listing page."""
    tree = LexborHTMLParser(html)
    results = []
    seen = set()

    for link in tree.css("a[href]"):
        href = link.attributes.get("href", "")
        if not _DRUG_HREF.match(href):
            continue

        name = _clean(link.text(strip=True))
        if not name:
            continue

        detail_url = urljoin(source_url, href)
        if detail_url in seen:
            continue

        parent = link.parent
        context = _clean(parent.text(separator=" | ", strip=True)) if parent else name
        english_name = _latin_line(context.replace(name, "", 1))

        results.append(
            {
                "name": name,
                "english_name": english_name,
                "detail_url": detail_url,
                "source_url": source_url,
            }
        )
        seen.add(detail_url)

    return results
