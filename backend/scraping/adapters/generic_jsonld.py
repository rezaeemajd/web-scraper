"""Conservative JSON-LD Product extractor for generic CDI sources.

It only emits records when schema.org Product evidence is present. It never
interprets arbitrary page text as a product, which keeps generic parsing safe
across unrelated source layouts.
"""

import json
from decimal import Decimal, InvalidOperation

from selectolax.lexbor import LexborHTMLParser


def _as_list(value):
    if isinstance(value, list):
        return value
    return [value] if value is not None else []


def _product_types(value):
    return {
        str(item).rsplit("/", 1)[-1].lower()
        for item in _as_list(value)
        if isinstance(item, (str, int, float))
    }


def _money(value):
    if value is None:
        return None
    text = str(value).strip().replace(",", "").replace("٬", "")
    try:
        return str(Decimal(text))
    except (InvalidOperation, ValueError):
        return None


def _brand(value):
    if isinstance(value, dict):
        return str(value.get("name") or "").strip()
    return str(value or "").strip()


def extract_jsonld_products(html, source_url):
    tree = LexborHTMLParser(html)
    results = []
    seen = set()

    for node in tree.css('script[type="application/ld+json"]'):
        raw = node.text(strip=True)
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except (TypeError, ValueError, json.JSONDecodeError):
            continue

        candidates = []
        if isinstance(payload, dict) and "@graph" in payload:
            candidates.extend(_as_list(payload.get("@graph")))
        else:
            candidates.extend(_as_list(payload))

        for item in candidates:
            if not isinstance(item, dict):
                continue
            if "product" not in _product_types(item.get("@type")):
                continue

            name = str(item.get("name") or "").strip()
            if not name:
                continue

            offers = _as_list(item.get("offers"))
            for offer in offers or [{}]:
                if not isinstance(offer, dict):
                    offer = {}

                url = str(offer.get("url") or item.get("url") or source_url).strip()
                key = (name, url)
                if key in seen:
                    continue

                results.append(
                    {
                        "name": name,
                        "brand": _brand(item.get("brand")),
                        "sku": str(item.get("sku") or "").strip(),
                        "detail_url": url,
                        "price": _money(offer.get("price")),
                        "currency": str(
                            offer.get("priceCurrency") or ""
                        ).strip().upper(),
                        "availability": str(
                            offer.get("availability") or ""
                        ).rsplit("/", 1)[-1].strip().lower(),
                        "source_url": source_url,
                        "observation_type": "retail_product",
                        "evidence_type": "schema.org/Product",
                    }
                )
                seen.add(key)

    return results
