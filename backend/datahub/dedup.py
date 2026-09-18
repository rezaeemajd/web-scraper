from decimal import Decimal

from .models import DedupCandidate, ExtractedRecord


_MIN_SIMILARITY = Decimal("0.7000")


def similarity(a, b):
    keys = set(a) & set(b)
    comparable = [k for k in keys if a.get(k) not in (None, "") or b.get(k) not in (None, "")]
    if not comparable:
        return Decimal("0.0000"), []

    matches = [
        k for k in comparable
        if a.get(k) not in (None, "") and a.get(k) == b.get(k)
    ]
    return Decimal(str(round(len(matches) / len(comparable), 4))), sorted(matches)


def find_candidates(record, limit=20):
    if limit <= 0:
        return []

    qs = (
        ExtractedRecord.objects
        .filter(entity_type=record.entity_type)
        .exclude(pk=record.pk)
        .exclude(fingerprint=record.fingerprint)
        .exclude(status=ExtractedRecord.Status.ARCHIVED)
        .order_by("pk")
    )

    candidates = []
    for other in qs.iterator():
        score, fields = similarity(record.normalized_payload, other.normalized_payload)
        if score < _MIN_SIMILARITY:
            continue

        left, right = sorted((record, other), key=lambda item: item.pk)
        candidate, created = DedupCandidate.objects.get_or_create(
            record_a=left,
            record_b=right,
            defaults={"similarity": score, "matched_fields": fields},
        )
        if not created and (
            candidate.similarity != score or candidate.matched_fields != fields
        ):
            candidate.similarity = score
            candidate.matched_fields = fields
            candidate.save(update_fields=["similarity", "matched_fields"])

        candidates.append(candidate)
        if len(candidates) >= limit:
            break

    return candidates
