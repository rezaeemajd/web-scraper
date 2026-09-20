import uuid

import redis
from celery import shared_task
from django.db import transaction
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from .engine import execute_many
from .models import Scraper, ScraperRun


class DuplicateScraperRun(RuntimeError):
    """Raised when a scraper already has an active task."""


class RetryableScraperRun(RuntimeError):
    """Raised when the last fetch failed with a transient network error."""


_LOCK_TTL_SECONDS = 50 * 60
_STALE_RUN_SECONDS = 50 * 60
_RELEASE_LOCK_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
end
return 0
"""


def _recover_stale_run(scraper_id):
    cutoff = timezone.now() - timedelta(seconds=_STALE_RUN_SECONDS)
    with transaction.atomic():
        stale = (
            ScraperRun.objects
            .select_for_update()
            .filter(
                scraper_id=scraper_id,
                status=ScraperRun.Status.RUNNING,
                started_at__lt=cutoff,
            )
        )
        stale.update(
            status=ScraperRun.Status.FAILED,
            finished_at=timezone.now(),
            error_message="worker lease expired; recovered as failed",
        )


def _scraper_lock(scraper_id):
    client = redis.Redis.from_url(settings.REDIS_URL)
    key = f"cdi:scraper-run:{scraper_id}"
    token = uuid.uuid4().hex
    acquired = client.set(key, token, nx=True, ex=_LOCK_TTL_SECONDS)
    if not acquired:
        client.close()
        raise DuplicateScraperRun("scraper already has an active run")
    return client, key, token


def _release_scraper_lock(client, key, token):
    try:
        client.eval(_RELEASE_LOCK_SCRIPT, 1, key, token)
    except redis.RedisError:
        # Lock expiry is the recovery mechanism; never mask the task result.
        pass
    finally:
        client.close()


@shared_task(
    bind=True,
    autoretry_for=(RetryableScraperRun,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=3,
)
def run_scraper(self, scraper_id):
    scraper = Scraper.objects.select_related("source", "entity_type").get(pk=scraper_id)
    if not scraper.active:
        raise ValueError("scraper is inactive")
    if not scraper.source.allowed or scraper.source.status != scraper.source.Status.ACTIVE:
        raise ValueError("source is not active")

    client, lock_key, lock_token = _scraper_lock(scraper_id)
    run = None
    try:
        _recover_stale_run(scraper_id)
        # Redis is the fast distributed guard. The row lock is the durable
        # second line of defense if a long-running task outlives the Redis TTL.
        with transaction.atomic():
            locked_scraper = Scraper.objects.select_for_update().get(pk=scraper_id)
            active_run = (
                ScraperRun.objects
                .filter(
                    scraper=locked_scraper,
                    status__in=(ScraperRun.Status.QUEUED, ScraperRun.Status.RUNNING),
                )
                .order_by("pk")
                .first()
            )
            if active_run is not None:
                raise DuplicateScraperRun("scraper already has an active run")
            run = ScraperRun.objects.create(
                scraper=locked_scraper,
                status=ScraperRun.Status.RUNNING,
                started_at=timezone.now(),
            )
        try:
            _, captures, record_count = execute_many(
                locked_scraper,
                collect_records=False,
            )
            run.pages_fetched = sum(
                1 for item in captures if item.status == item.Status.SUCCESS
            )
            run.records_extracted = record_count
            capture = captures[-1] if captures else None
            if capture is None:
                raise RuntimeError("scraper produced no capture")
            run.status = (
                ScraperRun.Status.SUCCESS
                if capture.status == capture.Status.SUCCESS
                else (
                    ScraperRun.Status.BLOCKED
                    if capture.status == capture.Status.BLOCKED
                    else ScraperRun.Status.FAILED
                )
            )
            if run.status == ScraperRun.Status.FAILED:
                run.error_message = capture.error_message
                if capture.error_message.startswith("transient:"):
                    raise RetryableScraperRun(capture.error_message)
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
    finally:
        _release_scraper_lock(client, lock_key, lock_token)
