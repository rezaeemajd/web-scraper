from django.db import transaction

from .models import AuditEvent, DedupCandidate, ExtractedRecord


@transaction.atomic
def resolve_dedup_candidate(*, candidate_id, status, winner_id=None, actor=None):
    candidate = DedupCandidate.objects.select_for_update().get(pk=candidate_id)
    if candidate.status != DedupCandidate.Status.OPEN:
        raise ValueError("candidate is already resolved")
    if status not in (DedupCandidate.Status.MERGED, DedupCandidate.Status.REJECTED):
        raise ValueError("invalid dedup resolution status")

    record_ids = sorted((candidate.record_a_id, candidate.record_b_id))
    locked = list(
        ExtractedRecord.objects.select_for_update().filter(pk__in=record_ids).order_by("pk")
    )
    records = {record.pk: record for record in locked}
    record_a = records[candidate.record_a_id]
    record_b = records[candidate.record_b_id]

    before = {
        "status": candidate.status,
        "record_a_status": record_a.status,
        "record_b_status": record_b.status,
    }
    metadata = {"record_a_id": candidate.record_a_id, "record_b_id": candidate.record_b_id}

    if status == DedupCandidate.Status.MERGED:
        if winner_id not in (candidate.record_a_id, candidate.record_b_id):
            raise ValueError("winner_id must reference one of the candidate records")

        winner = records[winner_id]
        loser = record_b if winner_id == candidate.record_a_id else record_a

        if winner.status == ExtractedRecord.Status.ARCHIVED:
            raise ValueError("winner record is archived")
        if loser.status == ExtractedRecord.Status.ARCHIVED:
            raise ValueError("loser record is already archived")

        loser.status = ExtractedRecord.Status.ARCHIVED
        loser.save(update_fields=["status", "updated_at"])
        metadata["winner_id"] = winner_id
        metadata["archived_id"] = loser.pk

    candidate.status = status
    candidate.save(update_fields=["status"])
    after = {
        "status": candidate.status,
        "record_a_status": record_a.status,
        "record_b_status": record_b.status,
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
