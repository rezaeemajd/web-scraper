from decimal import Decimal

from django.db.models import Case, IntegerField, Q, Value, When

from .models import DedupCandidate, EntityField, ExtractedRecord


_MIN_SIMILARITY = Decimal("0.7000")


def similarity(a, b):
    keys = set(a) & set(b)
    comparable = [
        k for k in keys
        if a.get(k) not in (None, "") or b.get(k) not in (None, "")
    ]
    if not comparable:
        return Decimal("0.0000"), []

    matches = [
        k for k in comparable
        if a.get(k) not in (None, "") and a.get(k) == b.get(k)
    ]
    return Decimal(str(round(len(matches) / len(comparable), 4))), sorted(matches)


def _candidate_queryset(record):
    base = (
        ExtractedRecord.objects
        .filter(entity_type=record.entity_type)
        .exclude(pk=record.pk)
        .exclude(fingerprint=record.fingerprint)
        .exclude(status=ExtractedRecord.Status.ARCHIVED)
        .only("id", "entity_type_id", "fingerprint", "status", "normalized_payload")
        .order_by("pk")
    )

    # Block first on searchable, non-empty fields. This turns the common case
    # from an O(N) Python scan into indexed/JSONB filtering in PostgreSQL.
    searchable = EntityField.objects.filter(
        entity_type=record.entity_type,
        searchable=True,
    ).values_list("slug", "name")
    payload = record.normalized_payload or {}
    blocks = []
    for slug, name in searchable:
        for key in (slug, name):
            value = payload.get(key)
            if value not in (None, ""):
                blocks.append(Q(normalized_payload__contains={key: value}))
                break

    if blocks:
        condition = blocks[0]
        for block in blocks[1:]:
            condition |= block

        # Rank candidates by how many blocking fields match before Python
        # similarity scoring. The hard cap prevents a common value such as a
        # generic clinic name from turning into an unbounded scan.
        score_terms = []
        for slug, name in searchable:
            for key in (slug, name):
                value = payload.get(key)
                if value not in (None, ""):
                    score_terms.append(
                        Case(
                            When(
                                normalized_payload__contains={key: value},
                                then=Value(1),
                            ),
                            default=Value(0),
                            output_field=IntegerField(),
                        )
                    )
                    break

        block_score = score_terms[0]
        for term in score_terms[1:]:
            block_score = block_score + term

        return (
            base.filter(condition)
            .annotate(_block_score=block_score)
            .order_by("-_block_score", "pk")[:1000]
        )

    # Schemas without searchable fields retain the previous complete-scan
    # behavior rather than silently losing candidates.
    return base


def find_candidates(record, limit=20):
    if limit <= 0:
        return []

    candidates = []
    for other in _candidate_queryset(record).iterator():
        score, fields = similarity(
            record.normalized_payload,
            other.normalized_payload,
        )
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
