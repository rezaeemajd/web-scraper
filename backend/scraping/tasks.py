import uuid

import redis
from celery import shared_task
from django.db import transaction
from django.conf import settings
from django.utils import timezone

from .engine import execute
from .models import Scraper, ScraperRun


class DuplicateScraperRun(RuntimeError):
    """Raised when a scraper already has an active task."""


_LOCK_TTL_SECONDS = 2 * 60 * 60
_RELEASE_LOCK_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
end
return 0
"""


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


@shared_task(bind=True)
def run_scraper(self, scraper_id):
    scraper = Scraper.objects.select_related("source", "entity_type").get(pk=scraper_id)
    if not scraper.active:
        raise ValueError("scraper is inactive")
    if not scraper.source.allowed or scraper.source.status != scraper.source.Status.ACTIVE:
        raise ValueError("source is not active")

    client, lock_key, lock_token = _scraper_lock(scraper_id)
    run = None
    try:
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
            record, capture = execute(locked_scraper)
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
    finally:
        _release_scraper_lock(client, lock_key, lock_token)
