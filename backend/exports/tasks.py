from celery import shared_task
from django.utils import timezone

from .engine import build_export
from .models import ExportJob


@shared_task(
    bind=True,
    autoretry_for=(OSError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=120,
    retry_jitter=True,
    max_retries=2,
)
def run_export(self, job_id):
    job = ExportJob.objects.get(pk=job_id)
    job.status = ExportJob.Status.RUNNING
    job.error_message = ""
    job.save(update_fields=["status", "error_message"])

    try:
        path = build_export(job)
    except Exception as exc:
        job.status = ExportJob.Status.FAILED
        job.error_message = str(exc)[:4000]
        job.save(update_fields=["status", "error_message"])
        raise

    job.file_path = str(path)
    job.status = ExportJob.Status.SUCCESS
    job.save(update_fields=["file_path", "status"])
    return {"job_id": job.pk, "status": job.status, "file_path": job.file_path}
