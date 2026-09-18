from selectolax.parser import HTMLParser

from .models import Scraper
from sources.fetcher import capture_url
from datahub.pipeline import process_record


class ScraperConfigError(ValueError):
    """Raised when a scraper extraction configuration is invalid."""


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
            raise ScraperConfigError(f"selector for {field!r} must be a non-empty string")
    return config


def extract_static_html(scraper: Scraper, html: str):
    config = validate_extraction_config(scraper.extraction_config or {})
    payload = {}
    evidence = []
    tree = HTMLParser(html)
    for field, selector in config["fields"].items():
        try:
            node = tree.css_first(selector)
        except Exception as exc:
            raise ScraperConfigError(
                f"invalid CSS selector for {field!r}: {exc}"
            ) from exc
        value = node.text(strip=True) if node else ""
        payload[field] = value
        evidence.append(
            {
                "field": field,
                "selector": selector,
                "value": value,
            }
        )
    return payload, evidence


def execute(scraper: Scraper):
    if not scraper.entity_type:
        raise ValueError("scraper.entity_type is required")
    capture = capture_url(scraper.source, scraper.start_url)
    if capture.status != capture.Status.SUCCESS:
        return None, capture
    payload, evidence = extract_static_html(scraper, capture.body)
    record = process_record(
        entity_type=scraper.entity_type,
        url=scraper.start_url,
        payload=payload,
        raw_capture=capture,
        evidence=evidence,
        source_domain=scraper.source.domain,
    )
    return record, capture
