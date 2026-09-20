import re

from selectolax.lexbor import LexborHTMLParser

from datahub.pipeline import normalize_text


_LABELS = {
    "province": ("استان",),
    "city": ("شهرستان", "شهر"),
    "address": ("آدرس",),
}


def _clean(value):
    return normalize_text(value or "").strip(" :،")


def _label_value(text, labels):
    for label in labels:
        match = re.search(
            rf"{re.escape(label)}\s*[:：]\s*(.+?)(?=\s+(?:استان|شهرستان|شهر|آدرس)\s*[:：]|$)",
            text,
            flags=re.DOTALL,
        )
        if match:
            return _clean(match.group(1))
    return ""


def extract_pharmacies(html, source_url):
    """Parse the stable semantic content of a Pillix pharmacy listing page.

    The parser intentionally does not infer drug availability. It extracts only
    pharmacy directory facts that are explicitly present in each card.
    """
    tree = LexborHTMLParser(html)
    results = []

    for heading in tree.css("h2"):
        title = _clean(heading.text(strip=True))
        if not title.startswith("داروخانه"):
            continue

        node = heading.parent
        selected = None
        for _ in range(5):
            if node is None:
                break
            text = _clean(node.text(separator=" ", strip=True))
            if (
                title in text
                and "استان" in text
                and "شهرستان" in text
                and "آدرس" in text
            ):
                selected = text
                break
            node = node.parent

        if not selected:
            continue

        item = {
            "name": title,
            "province": _label_value(selected, _LABELS["province"]),
            "city": _label_value(selected, _LABELS["city"]),
            "address": _label_value(selected, _LABELS["address"]),
            "source_url": source_url,
        }

        # Activity type is explicit text between the title and province.
        prefix = selected.split("استان", 1)[0]
        prefix = prefix.replace(title, "", 1).strip()
        if prefix:
            item["pharmacy_type"] = prefix

        if item["province"] and item["city"] and item["address"]:
            results.append(item)

    # Directory pages may repeat the same card in navigation/SEO blocks.
    unique = {}
    for item in results:
        key = (
            item["name"],
            item["province"],
            item["city"],
            item["address"],
        )
        unique.setdefault(key, item)
    return list(unique.values())
