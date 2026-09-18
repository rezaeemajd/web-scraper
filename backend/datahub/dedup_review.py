from django.db import transaction

from .models import AuditEvent, DedupCandidate, ExtractedRecord


@transaction.atomic
def resolve_dedup_candidate(*, candidate_id, status, winner_id=None, actor=None):
    candidate = DedupCandidate.objects.select_for_update().select_related("record_a", "record_b").get(pk=candidate_id)
    if candidate.status != DedupCandidate.Status.OPEN:
        raise ValueError("candidate is already resolved")
    if status not in (DedupCandidate.Status.MERGED, DedupCandidate.Status.REJECTED):
        raise ValueError("invalid dedup resolution status")

    before = {
        "status": candidate.status,
        "record_a_status": candidate.record_a.status,
        "record_b_status": candidate.record_b.status,
    }
    metadata = {"record_a_id": candidate.record_a_id, "record_b_id": candidate.record_b_id}

    if status == DedupCandidate.Status.MERGED:
        if winner_id not in (candidate.record_a_id, candidate.record_b_id):
            raise ValueError("winner_id must reference one of the candidate records")
        loser = candidate.record_b if winner_id == candidate.record_a_id else candidate.record_a
        loser.status = ExtractedRecord.Status.ARCHIVED
        loser.save(update_fields=["status", "updated_at"])
        metadata["winner_id"] = winner_id
        metadata["archived_id"] = loser.pk

    candidate.status = status
    candidate.save(update_fields=["status"])
    after = {
        "status": candidate.status,
        "record_a_status": candidate.record_a.status,
        "record_b_status": candidate.record_b.status,
    }
    AuditEvent.objects.create(
        actor=actor,
        action="dedup.resolve",
        entity="DedupCandidate",
        object_id=str(candidate.pk),
        before=before,
        after=after,
        metadata=metadata,
    )
    return candidate
