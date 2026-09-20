import pytest
from django.utils import timezone
from sources.models import Source
from datahub.models import EntityType
from .engine import execute_many, extract_static_html
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
        "scraping.tasks.execute_many",
        lambda scraper, **kwargs: (
            [
                __import__("datahub.models", fromlist=["ExtractedRecord"]).ExtractedRecord.objects.create(
                    entity_type=entity,
                    source_url=scraper.start_url,
                    source_domain=source.domain,
                    payload={"name": "دکتر الف"},
                    normalized_payload={"name": "دکتر الف"},
                    raw_capture=capture,
                    fingerprint="a" * 64,
                )
            ],
            [capture],
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
        "scraping.tasks.execute_many",
        lambda scraper, **kwargs: ([], [capture], 0),
    )

    result = run_scraper.run(scraper.pk)
    run = ScraperRun.objects.get(pk=result["run_id"])

    assert result["status"] == ScraperRun.Status.BLOCKED
    assert run.status == ScraperRun.Status.BLOCKED
    assert run.error_message == "robots.txt disallowed"


@pytest.mark.django_db
def test_extract_static_html_rejects_invalid_config():
    from .engine import ScraperConfigError, extract_static_html

    source = Source.objects.create(
        name="Config Source",
        domain="example.com",
        base_url="https://example.com",
        respect_robots=False,
    )
    scraper = Scraper.objects.create(
        name="Invalid config",
        source=source,
        start_url="https://example.com",
        extraction_config={"fields": {"name": "div["}},
    )

    with pytest.raises(ScraperConfigError, match="invalid CSS selector"):
        extract_static_html(scraper, "<html><div>x</div></html>")


@pytest.mark.django_db
def test_extract_static_html_requires_fields():
    from .engine import ScraperConfigError, extract_static_html

    source = Source.objects.create(
        name="Empty Config Source",
        domain="example.com",
        base_url="https://example.com",
        respect_robots=False,
    )
    scraper = Scraper.objects.create(
        name="Empty config",
        source=source,
        start_url="https://example.com",
        extraction_config={},
    )

    with pytest.raises(ScraperConfigError, match="fields"):
        extract_static_html(scraper, "<html></html>")


@pytest.mark.django_db
def test_extract_static_html_supports_multiple_records():
    source = Source.objects.create(
        name="Multi Source",
        domain="example.com",
        base_url="https://example.com",
        respect_robots=False,
    )
    entity = EntityType.objects.create(name="دارو چندتایی", slug="drug-multi")
    scraper = Scraper.objects.create(
        name="Multi scraper",
        source=source,
        start_url="https://example.com/drugs",
        entity_type=entity,
        extraction_config={
            "record_selector": ".drug",
            "fields": {"name": ".name", "price": ".price"},
        },
    )

    payloads, evidences = extract_static_html(
        scraper,
        '<div class="drug"><span class="name">آسپرین</span><span class="price">100</span></div>'
        '<div class="drug"><span class="name">استامینوفن</span><span class="price">200</span></div>',
    )

    assert payloads == [
        {"name": "آسپرین", "price": "100"},
        {"name": "استامینوفن", "price": "200"},
    ]
    assert evidences[1][0]["scope"] == "record:1"


@pytest.mark.django_db
def test_execute_many_follows_bounded_pagination_and_avoids_loops(monkeypatch):
    from datahub.models import RawCapture

    source = Source.objects.create(
        name="Pagination Source",
        domain="example.com",
        base_url="https://example.com",
        respect_robots=False,
    )
    entity = EntityType.objects.create(name="پزشک صفحه‌ای", slug="doctor-pages")
    scraper = Scraper.objects.create(
        name="Pagination scraper",
        source=source,
        start_url="https://example.com/page/1",
        entity_type=entity,
        extraction_config={
            "fields": {"name": ".name"},
            "pagination": {"next_selector": "a.next", "max_pages": 3},
        },
    )
    pages = {
        "https://example.com/page/1": '<div class="name">A</div><a class="next" href="/page/2">next</a>',
        "https://example.com/page/2": '<div class="name">B</div><a class="next" href="/page/2">loop</a>',
    }

    def fake_capture(source, url, *, client=None):
        return RawCapture(
            url=url,
            status_code=200,
            body=pages[url],
            status=RawCapture.Status.SUCCESS,
        )

    monkeypatch.setattr("scraping.engine.capture_url", fake_capture)
    records, captures = execute_many(scraper)

    assert len(records) == 2
    assert [capture.url for capture in captures] == [
        "https://example.com/page/1",
        "https://example.com/page/2",
    ]


def test_extract_static_html_many_uses_record_scope_only_for_multi_record_configs():
    scraper = type(
        "ScraperStub",
        (),
        {
            "extraction_config": {
                "record_selector": ".item",
                "fields": {"name": ".name"},
            }
        },
    )()
    payloads, evidences = extract_static_html(
        scraper,
        '<div class="item"><span class="name">A</span></div>'
        '<div class="item"><span class="name">B</span></div>',
    )
    assert payloads == [{"name": "A"}, {"name": "B"}]
    assert evidences[0][0]["scope"] == "record:0"
    assert evidences[1][0]["scope"] == "record:1"


@pytest.mark.django_db
def test_stale_running_scraper_run_is_recovered():
    from datetime import timedelta
    from django.utils import timezone
    from scraping.tasks import _recover_stale_run
    from scraping.models import ScraperRun

    source = Source.objects.create(
        name="Stale Run Source",
        domain="example.com",
        base_url="https://example.com",
        respect_robots=False,
    )
    entity = EntityType.objects.create(name="تست بازیابی", slug="stale-recovery")
    scraper = Scraper.objects.create(
        name="Stale recovery scraper",
        source=source,
        start_url="https://example.com/stale",
        entity_type=entity,
    )
    old = timezone.now() - timedelta(minutes=60)
    run = ScraperRun.objects.create(
        scraper=scraper,
        status=ScraperRun.Status.RUNNING,
        started_at=old,
    )
    _recover_stale_run(scraper.pk)
    run.refresh_from_db()
    assert run.status == ScraperRun.Status.FAILED
    assert "lease expired" in run.error_message


@pytest.mark.django_db
def test_execute_many_batches_duplicate_records_before_persisting(monkeypatch):
    from datahub.models import ExtractedRecord, RawCapture

    source = Source.objects.create(
        name="Batch Source",
        domain="example.com",
        base_url="https://example.com",
        respect_robots=False,
    )
    entity = EntityType.objects.create(name="داده تکراری", slug="batch-dedupe")
    scraper = Scraper.objects.create(
        name="Batch scraper",
        source=source,
        start_url="https://example.com/items",
        entity_type=entity,
        extraction_config={
            "record_selector": ".item",
            "fields": {"name": ".name"},
        },
    )
    capture = RawCapture(
        url=scraper.start_url,
        status_code=200,
        body=(
            '<div class="item"><span class="name">A</span></div>'
            '<div class="item"><span class="name">A</span></div>'
            '<div class="item"><span class="name">B</span></div>'
        ),
        status=RawCapture.Status.SUCCESS,
    )
    monkeypatch.setattr(
        "scraping.engine.capture_url",
        lambda source, url, *, client=None: capture,
    )

    records, captures = execute_many(scraper)

    assert len(captures) == 1
    assert len(records) == 3
    assert ExtractedRecord.objects.filter(entity_type=entity).count() == 2
    assert records[0].pk == records[1].pk
    assert records[2].pk != records[0].pk


@pytest.mark.django_db
def test_execute_many_can_skip_record_object_retention(monkeypatch):
    from datahub.models import ExtractedRecord, RawCapture

    source = Source.objects.create(
        name="Low Memory Source",
        domain="example.com",
        base_url="https://example.com",
        respect_robots=False,
    )
    entity = EntityType.objects.create(name="کم‌حافظه", slug="low-memory")
    scraper = Scraper.objects.create(
        name="Low memory scraper",
        source=source,
        start_url="https://example.com/items",
        entity_type=entity,
        extraction_config={
            "record_selector": ".item",
            "fields": {"name": ".name"},
        },
    )
    capture = RawCapture(
        url=scraper.start_url,
        status_code=200,
        body=(
            '<div class="item"><span class="name">A</span></div>'
            '<div class="item"><span class="name">B</span></div>'
        ),
        status=RawCapture.Status.SUCCESS,
    )
    monkeypatch.setattr(
        "scraping.engine.capture_url",
        lambda source, url, *, client=None: capture,
    )

    records, captures, count = execute_many(scraper, collect_records=False)

    assert records == []
    assert len(captures) == 1
    assert count == 2
    assert ExtractedRecord.objects.filter(entity_type=entity).count() == 2


@pytest.mark.django_db
def test_run_scraper_retries_transient_http_status(monkeypatch):
    from datahub.models import RawCapture
    from scraping.tasks import RetryableScraperRun, run_scraper
    from scraping.models import ScraperRun

    source = Source.objects.create(
        name="Transient Status Source",
        domain="example.com",
        base_url="https://example.com",
        respect_robots=False,
    )
    entity = EntityType.objects.create(name="وضعیت موقت", slug="transient-status")
    scraper = Scraper.objects.create(
        name="Transient status scraper",
        source=source,
        start_url="https://example.com/temporary",
        entity_type=entity,
    )
    capture = RawCapture(
        url=scraper.start_url,
        status_code=503,
        status=RawCapture.Status.ERROR,
        error_message="transient:http_status:503",
    )
    monkeypatch.setattr(
        "scraping.tasks.execute_many",
        lambda scraper, **kwargs: ([], [capture]),
    )

    with pytest.raises(RetryableScraperRun, match="transient:http_status:503"):
        run_scraper.run(scraper.pk)

    run = ScraperRun.objects.get(scraper=scraper)
    assert run.status == ScraperRun.Status.FAILED
    assert run.error_message == "transient:http_status:503"


@pytest.mark.django_db
def test_execute_many_can_stream_without_retaining_captures(monkeypatch):
    from datahub.models import RawCapture

    source = Source.objects.create(
        name="Streaming Capture Source",
        domain="example.com",
        base_url="https://example.com",
        respect_robots=False,
    )
    entity = EntityType.objects.create(name="استریم", slug="streaming-captures")
    scraper = Scraper.objects.create(
        name="Streaming capture scraper",
        source=source,
        start_url="https://example.com/page/1",
        entity_type=entity,
        extraction_config={
            "fields": {"name": ".name"},
            "pagination": {"next_selector": "a.next", "max_pages": 2},
        },
    )
    pages = {
        "https://example.com/page/1": '<div class="name">A</div><a class="next" href="/page/2">next</a>',
        "https://example.com/page/2": '<div class="name">B</div>',
    }

    def fake_capture(source, url, *, client=None):
        return RawCapture(
            url=url,
            status_code=200,
            body=pages[url],
            status=RawCapture.Status.SUCCESS,
        )

    progress = []
    monkeypatch.setattr("scraping.engine.capture_url", fake_capture)

    records, captures, count = execute_many(
        scraper,
        collect_records=False,
        collect_captures=False,
        progress_callback=lambda capture, pages_fetched, record_count: progress.append(
            (capture.url, pages_fetched, record_count)
        ),
    )

    assert records == []
    assert captures == []
    assert count == 2
    assert progress == [
        ("https://example.com/page/1", 1, 1),
        ("https://example.com/page/2", 2, 2),
    ]


def test_scraper_lock_refresh_requires_same_token():
    from scraping import tasks

    class FakeRedis:
        def __init__(self, result):
            self.result = result
            self.calls = []

        def eval(self, script, key_count, key, token, ttl):
            self.calls.append((script, key_count, key, token, ttl))
            return self.result

    client = FakeRedis(1)
    tasks._refresh_scraper_lock(client, "lock:key", "token")
    assert client.calls[0][2:] == ("lock:key", "token", tasks._LOCK_TTL_SECONDS)

    lost = FakeRedis(0)
    with pytest.raises(tasks.DuplicateScraperRun, match="lock lease was lost"):
        tasks._refresh_scraper_lock(lost, "lock:key", "token")
