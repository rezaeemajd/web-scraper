import pytest
from sources.models import Source
from datahub.models import EntityType
from .engine import extract_static_html
from .models import Scraper


@pytest.mark.django_db
def test_static_html_extraction_captures_payload_and_evidence():
    source = Source.objects.create(name="Example", domain="example.com", base_url="https://example.com")
    entity = EntityType.objects.create(name="دارو", slug="drug")
    scraper = Scraper.objects.create(
        name="Drug page",
        source=source,
        start_url="https://example.com/drug/1",
        entity_type=entity,
        extraction_config={"fields": {"name": "h1.name", "price": ".price"}},
    )

    payload, evidence = extract_static_html(
        scraper,
        "<html><h1 class='name'>  Aspirin </h1><div class='price'>12000</div></html>",
    )

    assert payload == {"name": "Aspirin", "price": "12000"}
    assert evidence[0]["field"] == "name"
    assert evidence[0]["selector"] == "h1.name"
    assert evidence[0]["value"] == "Aspirin"


def test_extraction_config_missing_selector_returns_empty_value():
    scraper = type("ScraperStub", (), {"extraction_config": {"fields": {"name": ".missing"}}})()
    payload, evidence = extract_static_html(scraper, "<html><h1>Nothing</h1></html>")
    assert payload == {"name": ""}
    assert evidence == [{"field": "name", "selector": ".missing", "value": ""}]
