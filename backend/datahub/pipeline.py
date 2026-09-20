import hashlib
import json
from decimal import Decimal
from urllib.parse import urlsplit


from .models import ExtractedRecord


def normalize_text(value):
    if not isinstance(value, str):
        return value
    return " ".join(
        value.replace("ي", "ی")
        .replace("ى", "ی")
        .replace("ك", "ک")
        .replace("ۀ", "هٔ")
        .split()
    )


def normalize_value(value):
    if isinstance(value, dict):
        return {str(k): normalize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize_value(v) for v in value]
    return normalize_text(value)


def canonical_url(url):
    p = urlsplit(url)
    scheme = p.scheme.lower()
    host = (p.hostname or "").lower()
    path = p.path or "/"
    path = path.rstrip("/") or "/"
    return f"{scheme}://{host}{path}" + (f"?{p.query}" if p.query else "")


def fingerprint(payload):
    raw = json.dumps(
        normalize_value(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(raw.encode()).hexdigest()


def validate_payload(entity_type, payload, *, fields=None):
    fields = list(fields) if fields is not None else list(entity_type.fields.all())
    return [
        {"field": field.slug, "code": "required"}
        for field in fields
        if field.required and payload.get(field.slug) in (None, "", [])
    ]


def quality_score(payload, entity_type, errors, *, fields=None):
    fields = list(fields) if fields is not None else list(entity_type.fields.all())
    if not fields:
        return Decimal("0.0000")
    filled = sum(
        1 for field in fields
        if payload.get(field.slug) not in (None, "", [])
    )
    penalty = min(0.5, len(errors) * 0.1)
    return Decimal(str(round(max(0.0, filled / len(fields) - penalty), 4)))


def _build_values(
    *,
    entity_type,
    url,
    payload,
    raw_capture,
    evidence,
    source_domain,
    fields,
):
    normalized = normalize_value(payload)
    errors = validate_payload(entity_type, normalized, fields=fields)
    score = quality_score(normalized, entity_type, errors, fields=fields)
    return {
        "raw_capture": raw_capture,
        "source_url": canonical_url(url),
        "source_domain": source_domain
        or (urlsplit(url).hostname or "").lower(),
        "payload": payload,
        "normalized_payload": normalized,
        "evidence": evidence or [],
        "confidence": score,
        "quality_score": score,
        "fingerprint": fingerprint(normalized),
        "validation_errors": errors,
        "status": (
            ExtractedRecord.Status.REVIEW
            if errors
            else ExtractedRecord.Status.PARSED
        ),
    }


def process_records(
    *,
    entity_type,
    items,
    fields=None,
    batch_size=100,
):
    """Persist many extracted observations with one lookup and batched inserts.

    Existing fingerprints are intentionally left unchanged: the canonical record
    is immutable for this ingestion pass, while raw capture/evidence remain
    attached to the first observation. The returned list preserves input order.
    """
    items = list(items)
    if not items:
        return []

    fields = list(fields) if fields is not None else list(entity_type.fields.all())
    values_list = [
        _build_values(
            entity_type=entity_type,
            url=item["url"],
            payload=item["payload"],
            raw_capture=item.get("raw_capture"),
            evidence=item.get("evidence"),
            source_domain=item.get("source_domain"),
            fields=fields,
        )
        for item in items
    ]

    # Collapse duplicate fingerprints inside the same page before INSERT. This
    # avoids unnecessary unique-index work for repeated cards/rows.
    unique_values = {}
    for values in values_list:
        unique_values.setdefault(values["fingerprint"], values)

    fingerprints = list(unique_values)
    existing = {
        record.fingerprint: record
        for record in ExtractedRecord.objects.filter(
            entity_type=entity_type,
            fingerprint__in=fingerprints,
        )
    }

    missing = [
        values for fp, values in unique_values.items()
        if fp not in existing
    ]
    if missing:
        new_records = [
            ExtractedRecord(entity_type=entity_type, **values)
            for values in missing
        ]
        # Ignore only uniqueness races: all model fields are populated,
        # and the fingerprint constraint is the intended idempotency key.
        # This lets the whole batch succeed even when another worker inserts
        # one of the same fingerprints concurrently.
        ExtractedRecord.objects.bulk_create(
            new_records,
            batch_size=max(1, int(batch_size)),
            ignore_conflicts=True,
        )

        existing.update({
            record.fingerprint: record
            for record in ExtractedRecord.objects.filter(
                entity_type=entity_type,
                fingerprint__in=fingerprints,
            )
        })

    resolved = [existing[values["fingerprint"]] for values in values_list]

    # Preserve every scrape observation without mutating the canonical record.
    # RawCapture is the immutable page-level provenance anchor.
    from .models import RecordObservation

    observations = [
        RecordObservation(
            record=record,
            raw_capture=values["raw_capture"],
            source_url=values["source_url"],
            source_domain=values["source_domain"],
            payload=values["payload"],
            normalized_payload=values["normalized_payload"],
            evidence=values["evidence"],
            fingerprint=values["fingerprint"],
        )
        for record, values in zip(resolved, values_list)
        if values["raw_capture"] is not None
    ]
    if observations:
        RecordObservation.objects.bulk_create(
            observations,
            batch_size=max(1, int(batch_size)),
            ignore_conflicts=True,
        )

    return resolved


def process_record(
    *,
    entity_type,
    url,
    payload,
    raw_capture=None,
    evidence=None,
    source_domain=None,
    fields=None,
):
    return process_records(
        entity_type=entity_type,
        items=[{
            "url": url,
            "payload": payload,
            "raw_capture": raw_capture,
            "evidence": evidence,
            "source_domain": source_domain,
        }],
        fields=fields,
    )[0]
