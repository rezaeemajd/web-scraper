from decimal import Decimal

from django.db.models import Case, IntegerField, Q, Value, When

from .models import DedupCandidate, EntityField, ExtractedRecord


_MIN_SIMILARITY = Decimal("0.7000")
_MAX_CANDIDATE_SCAN = 1000


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


def _blocking_fields(record):
    """Return configured searchable keys and non-empty values once."""
    payload = record.normalized_payload or {}
    fields = list(
        EntityField.objects.filter(
            entity_type=record.entity_type,
            is_blocking=True,
        ).values_list("slug", "name")
    )
    if not fields:
        fields = list(
            EntityField.objects.filter(
                entity_type=record.entity_type,
                searchable=True,
            ).values_list("slug", "name")
        )
    blocks = []
    for slug, name in fields:
        for key in (slug, name):
            value = payload.get(key)
            if value not in (None, ""):
                blocks.append((key, value))
                break
    return blocks


def _candidate_queryset(record, blocks=None):
    base = (
        ExtractedRecord.objects
        .filter(entity_type_id=record.entity_type_id)
        .exclude(pk=record.pk)
        .exclude(status=ExtractedRecord.Status.ARCHIVED)
        .only("id", "entity_type_id", "fingerprint", "status", "normalized_payload")
        .order_by("pk")
    )

    # Empty fingerprints are intentionally not treated as an idempotency key.
    if record.fingerprint:
        base = base.exclude(fingerprint=record.fingerprint)

    blocks = _blocking_fields(record) if blocks is None else blocks
    if not blocks:
        return base

    # Block first on searchable, non-empty fields. This turns the common case
    # from an O(N) Python scan into JSONB containment filtering in PostgreSQL.
    condition = Q()
    score_terms = []
    for key, value in blocks:
        match = Q(normalized_payload__contains={key: value})
        condition |= match
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

    block_score = score_terms[0]
    for term in score_terms[1:]:
        block_score = block_score + term

    # A bounded candidate set prevents a common value (for example, a generic
    # clinic name) from causing an unbounded Python similarity scan. Candidates
    # are ranked by the number of blocking-field matches before the final score.
    return (
        base.filter(condition)
        .annotate(_block_score=block_score)
        .order_by("-_block_score", "pk")[:_MAX_CANDIDATE_SCAN]
    )


def find_candidates(record, limit=20):
    if limit <= 0:
        return []

    blocks = _blocking_fields(record)
    queryset = _candidate_queryset(record, blocks=blocks)

    matches = []
    for other in queryset.iterator():
        score, fields = similarity(
            record.normalized_payload,
            other.normalized_payload,
        )
        if score >= _MIN_SIMILARITY:
            left, right = sorted((record, other), key=lambda item: item.pk)
            matches.append((left.pk, right.pk, score, fields))
            if len(matches) >= limit:
                break

    if not matches:
        return []

    # Resolve existing candidates in one query instead of get_or_create() once
    # per match. This is important when one source page produces many near
    # duplicates: DB round-trips now scale with batches, not candidate count.
    pairs = [(left_id, right_id) for left_id, right_id, _, _ in matches]
    existing = {
        (candidate.record_a_id, candidate.record_b_id): candidate
        for candidate in DedupCandidate.objects.filter(
            record_a_id__in=[left for left, _ in pairs],
            record_b_id__in=[right for _, right in pairs],
        )
    }

    to_create = []
    to_update = []
    result = []
    for left_id, right_id, score, fields in matches:
        key = (left_id, right_id)
        candidate = existing.get(key)
        if candidate is None:
            candidate = DedupCandidate(
                record_a_id=left_id,
                record_b_id=right_id,
                similarity=score,
                matched_fields=fields,
            )
            to_create.append(candidate)
        elif candidate.similarity != score or candidate.matched_fields != fields:
            candidate.similarity = score
            candidate.matched_fields = fields
            to_update.append(candidate)
        result.append(candidate)

    if to_create:
        DedupCandidate.objects.bulk_create(
            to_create,
            batch_size=min(100, len(to_create)),
            ignore_conflicts=True,
        )
        # A concurrent worker may have won the unique pair race. Re-read all
        # requested pairs so the returned objects always represent DB state.
        existing.update({
            (candidate.record_a_id, candidate.record_b_id): candidate
            for candidate in DedupCandidate.objects.filter(
                record_a_id__in=[left for left, _ in pairs],
                record_b_id__in=[right for _, right in pairs],
            )
        })
        result = [existing[(left, right)] for left, right, _, _ in matches]

    if to_update:
        DedupCandidate.objects.bulk_update(
            to_update,
            ["similarity", "matched_fields"],
            batch_size=min(100, len(to_update)),
        )

    # Preserve similarity order produced by the database scan and apply the
    # caller's limit only after scoring, so weak early blocks do not consume it.
    return result[:limit]
