from urllib.parse import urljoin

import httpx

from selectolax.lexbor import LexborHTMLParser

from .models import Scraper
from sources.fetcher import capture_url
from datahub.pipeline import process_records


class ScraperConfigError(ValueError):
    """Raised when a scraper extraction configuration is invalid."""


_MAX_PAGES = 100
_RECORD_BATCH_SIZE = 100


def validate_extraction_config(config):
    if not isinstance(config, dict):
        raise ScraperConfigError("extraction_config must be an object")

    fields = config.get("fields")
    if not isinstance(fields, dict) or not fields:
        raise ScraperConfigError("extraction_config.fields must be a non-empty object")

    for field, selector in fields.items():
        if not isinstance(field, str) or not field.strip():
            raise ScraperConfigError("field names must be non-empty strings")
        if not isinstance(selector, str) or not selector.strip():
            raise ScraperConfigError(
                f"selector for {field!r} must be a non-empty string"
            )

    record_selector = config.get("record_selector")
    if record_selector is not None and (
        not isinstance(record_selector, str) or not record_selector.strip()
    ):
        raise ScraperConfigError("record_selector must be a non-empty string")

    pagination = config.get("pagination") or {}
    if not isinstance(pagination, dict):
        raise ScraperConfigError("pagination must be an object")

    next_selector = pagination.get("next_selector")
    if next_selector is not None and (
        not isinstance(next_selector, str) or not next_selector.strip()
    ):
        raise ScraperConfigError("pagination.next_selector must be a non-empty string")

    max_pages = pagination.get("max_pages", 1)
    if isinstance(max_pages, bool) or not isinstance(max_pages, int):
        raise ScraperConfigError("pagination.max_pages must be an integer")
    if not 1 <= max_pages <= _MAX_PAGES:
        raise ScraperConfigError(
            f"pagination.max_pages must be between 1 and {_MAX_PAGES}"
        )

    return config


def _extract_payload(node, fields, evidence_prefix=""):
    payload = {}
    evidence = []
    for field, selector in fields.items():
        try:
            match = node.css_first(selector)
        except Exception as exc:
            raise ScraperConfigError(
                f"invalid CSS selector for {field!r}: {exc}"
            ) from exc

        value = match.text(strip=True) if match else ""
        payload[field] = value
        item = {
            "field": field,
            "selector": selector,
            "value": value,
        }
        if evidence_prefix:
            item["scope"] = evidence_prefix
        evidence.append(item)
    return payload, evidence


def _extract_static_html_many(config, html):
    tree = LexborHTMLParser(html)
    record_selector = config.get("record_selector")

    if record_selector:
        try:
            nodes = tree.css(record_selector)
        except Exception as exc:
            raise ScraperConfigError(
                f"invalid record_selector: {exc}"
            ) from exc
    else:
        nodes = [tree]

    payloads = []
    evidences = []
    for index, node in enumerate(nodes):
        payload, evidence = _extract_payload(
            node,
            config["fields"],
            evidence_prefix=f"record:{index}" if record_selector else "",
        )
        payloads.append(payload)
        evidences.append(evidence)
    return payloads, evidences


def extract_static_html_many(scraper: Scraper, html: str):
    config = validate_extraction_config(scraper.extraction_config or {})
    return _extract_static_html_many(config, html)


def extract_static_html(scraper: Scraper, html: str):
    """Backward-compatible single-record API; multi-record configs return lists."""
    config = validate_extraction_config(scraper.extraction_config or {})
    payloads, evidences = _extract_static_html_many(config, html)
    if config.get("record_selector"):
        return payloads, evidences
    return payloads[0], evidences[0]


def _next_page_url(config, html, current_url):
    pagination = config.get("pagination") or {}
    selector = pagination.get("next_selector")
    if not selector:
        return None

    tree = LexborHTMLParser(html)
    try:
        node = tree.css_first(selector)
    except Exception as exc:
        raise ScraperConfigError(
            f"invalid pagination.next_selector: {exc}"
        ) from exc
    if not node:
        return None

    href = node.attributes.get("href")
    if not href:
        return None
    return urljoin(current_url, href)


def execute_many(scraper: Scraper):
    if not scraper.entity_type:
        raise ValueError("scraper.entity_type is required")

    config = validate_extraction_config(scraper.extraction_config or {})
    max_pages = (config.get("pagination") or {}).get("max_pages", 1)

    current_url = scraper.start_url
    visited = set()
    records = []
    captures = []
    entity_fields = list(scraper.entity_type.fields.all())

    with httpx.Client(
        timeout=httpx.Timeout(20.0, connect=10.0),
        follow_redirects=False,
        trust_env=False,
        headers={"User-Agent": scraper.source.user_agent},
    ) as client:
        for _ in range(max_pages):
            if current_url in visited:
                break
            visited.add(current_url)

            capture = capture_url(scraper.source, current_url, client=client)
            captures.append(capture)
            if capture.status != capture.Status.SUCCESS:
                break

            payloads, evidences = _extract_static_html_many(config, capture.body)
            page_items = [
                {
                    "url": current_url,
                    "payload": payload,
                    "raw_capture": capture,
                    "evidence": evidence,
                    "source_domain": scraper.source.domain,
                }
                for payload, evidence in zip(payloads, evidences)
            ]
            records.extend(
                process_records(
                    entity_type=scraper.entity_type,
                    items=page_items,
                    fields=entity_fields,
                    batch_size=_RECORD_BATCH_SIZE,
                )
            )

            next_url = _next_page_url(config, capture.body, current_url)
            if not next_url:
                break
            current_url = next_url

    return records, captures


def execute(scraper: Scraper):
    records, captures = execute_many(scraper)
    return (records[0] if records else None), (captures[-1] if captures else None)
