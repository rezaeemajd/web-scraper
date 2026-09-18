from celery import shared_task
from django.utils import timezone

from .engine import execute
from .models import Scraper, ScraperRun


@shared_task(bind=True)
def run_scraper(self, scraper_id):
    scraper = Scraper.objects.select_related("source", "entity_type").get(pk=scraper_id)
    if not scraper.active:
        raise ValueError("scraper is inactive")
    if not scraper.source.allowed or scraper.source.status != scraper.source.Status.ACTIVE:
        raise ValueError("source is not active")

    run = ScraperRun.objects.create(
        scraper=scraper,
        status=ScraperRun.Status.RUNNING,
        started_at=timezone.now(),
    )
    try:
        record, capture = execute(scraper)
        run.pages_fetched = 1
        run.records_extracted = 1 if record else 0
        run.status = (
            ScraperRun.Status.SUCCESS
            if capture.status == capture.Status.SUCCESS
            else ScraperRun.Status.FAILED
        )
        if run.status == ScraperRun.Status.FAILED:
            run.error_message = capture.error_message
    except Exception as exc:
        run.status = ScraperRun.Status.FAILED
        run.error_message = str(exc)[:4000]
        raise
    finally:
        run.finished_at = timezone.now()
        run.save(
            update_fields=[
                "status",
                "started_at",
                "finished_at",
                "pages_fetched",
                "records_extracted",
                "error_message",
            ]
        )
    return {
        "run_id": run.id,
        "status": run.status,
        "records_extracted": run.records_extracted,
    }
