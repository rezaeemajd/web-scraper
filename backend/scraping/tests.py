import pytest
from django.utils import timezone
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


@pytest.mark.django_db
def test_execute_runs_capture_extraction_and_record_pipeline(monkeypatch):
    from datahub.models import ExtractedRecord, RawCapture
    from . import engine

    source = Source.objects.create(name="Example Pipeline", domain="example.com", base_url="https://example.com")
    entity = EntityType.objects.create(name="کلینیک", slug="clinic")
    scraper = Scraper.objects.create(
        name="Clinic page",
        source=source,
        start_url="https://example.com/clinic/1",
        entity_type=entity,
        extraction_config={"fields": {"name": "h1.name", "city": ".city"}},
    )
    capture = RawCapture.objects.create(
        url=scraper.start_url,
        status_code=200,
        content_type="text/html",
        body="<html><h1 class='name'>  درمانگاه كاشان </h1><div class='city'> كاشان </div></html>",
        status=RawCapture.Status.SUCCESS,
    )

    monkeypatch.setattr(engine, "capture_url", lambda source, url: capture)

    record, returned_capture = engine.execute(scraper)

    assert returned_capture.pk == capture.pk
    assert record is not None
    record.refresh_from_db()
    assert record.payload["name"] == "درمانگاه كاشان"
    assert record.normalized_payload["name"] == "درمانگاه کاشان"
    assert record.normalized_payload["city"] == "کاشان"
    assert record.raw_capture_id == capture.pk
    assert record.source_domain == "example.com"
    assert record.evidence[0]["selector"] == "h1.name"
    assert ExtractedRecord.objects.filter(pk=record.pk).exists()


@pytest.mark.django_db
def test_run_scraper_records_success(monkeypatch):
    from datahub.models import RawCapture
    from .tasks import run_scraper
    from .models import ScraperRun

    source = Source.objects.create(
        name="Task Source",
        domain="example.com",
        base_url="https://example.com",
        respect_robots=False,
    )
    entity = EntityType.objects.create(name="پزشک", slug="doctor-task")
    scraper = Scraper.objects.create(
        name="Task scraper",
        source=source,
        start_url="https://example.com/doctor/1",
        entity_type=entity,
        extraction_config={"fields": {"name": "h1.name"}},
    )
    capture = RawCapture.objects.create(
        url=scraper.start_url,
        status_code=200,
        content_type="text/html",
        body="<h1 class='name'>دکتر الف</h1>",
        status=RawCapture.Status.SUCCESS,
    )
    monkeypatch.setattr(
        "scraping.tasks.execute",
        lambda scraper: (
            __import__("datahub.models", fromlist=["ExtractedRecord"]).ExtractedRecord.objects.create(
                entity_type=entity,
                source_url=scraper.start_url,
                source_domain=source.domain,
                payload={"name": "دکتر الف"},
                normalized_payload={"name": "دکتر الف"},
                raw_capture=capture,
                fingerprint="a" * 64,
            ),
            capture,
        ),
    )

    result = run_scraper.run(scraper.pk)

    run = ScraperRun.objects.get(pk=result["run_id"])
    assert result["status"] == ScraperRun.Status.SUCCESS
    assert run.status == ScraperRun.Status.SUCCESS
    assert run.pages_fetched == 1
    assert run.records_extracted == 1
    assert run.finished_at is not None


@pytest.mark.django_db
def test_run_scraper_rejects_inactive_scraper():
    from .tasks import run_scraper
    from .models import ScraperRun

    source = Source.objects.create(
        name="Inactive Task Source",
        domain="example.com",
        base_url="https://example.com",
        respect_robots=False,
    )
    entity = EntityType.objects.create(name="کلینیک", slug="clinic-task")
    scraper = Scraper.objects.create(
        name="Inactive scraper",
        source=source,
        start_url="https://example.com/clinic/1",
        entity_type=entity,
        active=False,
    )

    with pytest.raises(ValueError, match="scraper is inactive"):
        run_scraper.run(scraper.pk)

    assert not ScraperRun.objects.filter(scraper=scraper).exists()


@pytest.mark.django_db
def test_run_scraper_rejects_inactive_source_without_creating_run():
    from .tasks import run_scraper
    from .models import ScraperRun

    source = Source.objects.create(
        name="Paused Task Source",
        domain="example.com",
        base_url="https://example.com",
        status=Source.Status.PAUSED,
        respect_robots=False,
    )
    entity = EntityType.objects.create(name="داروخانه", slug="pharmacy-task")
    scraper = Scraper.objects.create(
        name="Paused source scraper",
        source=source,
        start_url="https://example.com/pharmacy/1",
        entity_type=entity,
    )

    with pytest.raises(ValueError, match="source is not active"):
        run_scraper.run(scraper.pk)

    assert not ScraperRun.objects.filter(scraper=scraper).exists()

@pytest.mark.django_db
def test_run_scraper_blocks_existing_active_run_even_without_redis_lock(
    monkeypatch,
):
    from . import tasks
    from .models import ScraperRun

    source = Source.objects.create(
        name="Duplicate Guard Source",
        domain="example.com",
        base_url="https://example.com",
        respect_robots=False,
    )
    entity = EntityType.objects.create(name="بیمارستان", slug="hospital-duplicate")
    scraper = Scraper.objects.create(
        name="Duplicate guard scraper",
        source=source,
        start_url="https://example.com/hospital/1",
        entity_type=entity,
    )
    existing = ScraperRun.objects.create(
        scraper=scraper,
        status=ScraperRun.Status.RUNNING,
        started_at=timezone.now(),
    )

    monkeypatch.setattr(tasks, "_scraper_lock", lambda scraper_id: (object(), "key", "token"))
    monkeypatch.setattr(tasks, "_release_scraper_lock", lambda client, key, token: None)

    with pytest.raises(tasks.DuplicateScraperRun, match="active run"):
        tasks.run_scraper.run(scraper.pk)

    assert ScraperRun.objects.filter(
        scraper=scraper,
        status=ScraperRun.Status.RUNNING,
    ).count() == 1
    assert ScraperRun.objects.get(pk=existing.pk).finished_at is None


@pytest.mark.django_db
def test_run_scraper_records_blocked_capture_as_blocked(monkeypatch):
    from datahub.models import RawCapture
    from .tasks import run_scraper
    from .models import ScraperRun

    source = Source.objects.create(
        name="Blocked Task Source",
        domain="example.com",
        base_url="https://example.com",
        respect_robots=False,
    )
    entity = EntityType.objects.create(name="مرکز درمانی", slug="clinic-blocked")
    scraper = Scraper.objects.create(
        name="Blocked scraper",
        source=source,
        start_url="https://example.com/blocked",
        entity_type=entity,
    )
    capture = RawCapture.objects.create(
        url=scraper.start_url,
        status=RawCapture.Status.BLOCKED,
        error_message="robots.txt disallowed",
    )
    monkeypatch.setattr(
        "scraping.tasks.execute",
        lambda scraper: (None, capture),
    )

    result = run_scraper.run(scraper.pk)
    run = ScraperRun.objects.get(pk=result["run_id"])

    assert result["status"] == ScraperRun.Status.BLOCKED
    assert run.status == ScraperRun.Status.BLOCKED
    assert run.error_message == "robots.txt disallowed"
