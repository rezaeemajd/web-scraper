"""Source-specific parser for Darukade product listing pages.

Darukade is treated as a commercial retail observation source. Product listing
pages expose product links, names, brands and current retail price text; those
facts are observations from this source, not national registration truth.
"""

import re
from urllib.parse import urljoin

from selectolax.lexbor import LexborHTMLParser

from datahub.pipeline import normalize_text


_PRODUCT_HREF = re.compile(r"^/products/[^?#]+", re.IGNORECASE)
_PRICE = re.compile(r"([\d۰-۹][\d۰-۹,٬.\s]*)\s*تومان")


def _clean(value):
    return normalize_text(value or "").strip()


def _price_text(value):
    match = _PRICE.search(value or "")
    return match.group(1).strip() + " تومان" if match else ""


def extract_products(html, source_url):
    tree = LexborHTMLParser(html)
    results = []
    seen = set()

    for link in tree.css("a[href]"):
        href = link.attributes.get("href", "")
        if not _PRODUCT_HREF.match(href):
            continue

        name = _clean(link.text(strip=True))
        if not name:
            continue

        detail_url = urljoin(source_url, href)
        if detail_url in seen:
            continue

        card = link.parent
        context = _clean(card.text(separator=" | ", strip=True)) if card else name
        brand = ""
        siblings = card.css("a") if card else []
        for sibling in siblings:
            value = _clean(sibling.text(strip=True))
            if value and value != name and not _PRODUCT_HREF.match(
                sibling.attributes.get("href", "")
            ):
                brand = value
                break

        results.append(
            {
                "name": name,
                "brand": brand,
                "price_text": _price_text(context),
                "detail_url": detail_url,
                "source_url": source_url,
                "observation_type": "retail_listing",
            }
        )
        seen.add(detail_url)

    return results
