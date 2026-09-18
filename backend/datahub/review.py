from django.db import transaction

from .models import AuditEvent, ExtractedRecord, ReviewTask


ALLOWED_TRANSITIONS = {
    ReviewTask.Status.OPEN: {
        ReviewTask.Status.APPROVED,
        ReviewTask.Status.REJECTED,
        ReviewTask.Status.SKIPPED,
    }
}


@transaction.atomic
def transition_review_task(*, task_id, status, actor=None, notes=None):
    task = ReviewTask.objects.select_for_update().select_related("record").get(pk=task_id)
    if status not in ReviewTask.Status.values:
        raise ValueError("invalid review status")
    if status not in ALLOWED_TRANSITIONS.get(task.status, set()):
        raise ValueError(f"invalid transition: {task.status} -> {status}")

    before = {
        "review_status": task.status,
        "record_status": task.record.status,
        "notes": task.notes,
    }
    task.status = status
    if notes is not None:
        task.notes = notes
    task.save(update_fields=["status", "notes", "updated_at"])

    record_status = {
        ReviewTask.Status.APPROVED: ExtractedRecord.Status.APPROVED,
        ReviewTask.Status.REJECTED: ExtractedRecord.Status.REJECTED,
    }.get(status)
    if record_status:
        task.record.status = record_status
        task.record.save(update_fields=["status", "updated_at"])

    after = {
        "review_status": task.status,
        "record_status": task.record.status,
        "notes": task.notes,
    }
    AuditEvent.objects.create(
        actor=actor,
        action="review.transition",
        entity="ReviewTask",
        object_id=str(task.pk),
        before=before,
        after=after,
        metadata={"record_id": task.record_id},
    )
    return task
