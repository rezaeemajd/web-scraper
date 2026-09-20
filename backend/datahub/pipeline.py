import hashlib
import json
from decimal import Decimal
from urllib.parse import urlsplit


from .models import ExtractedRecord, RecordChange, RecordObservation


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


def canonical_identity_key(entity_type, normalized_payload, *, fields):
    """Build a stable entity identity from explicitly configured identifier fields.

    Returns an empty key when no identifier configuration exists or any configured
    identifier is missing. Mutable fields therefore never change the canonical
    identity; they only change the observation fingerprint.
    """
    identity_fields = [field for field in fields if field.is_identifier]
    if not identity_fields:
        return ""

    identity = {}
    for field in identity_fields:
        value = normalized_payload.get(field.slug)
        if value in (None, "", []):
            return ""
        identity[field.slug] = value

    raw = json.dumps(
        {"entity_type": entity_type.slug, "identity": identity},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return "idv1:" + hashlib.sha256(raw.encode()).hexdigest()
def _diff_payload(before, after, prefix=""):
    changes = []
    before = before if isinstance(before, dict) else {}
    after = after if isinstance(after, dict) else {}
    for key in sorted(set(before) | set(after)):
        path = f"{prefix}.{key}" if prefix else str(key)
        old = before.get(key)
        new = after.get(key)
        if isinstance(old, dict) and isinstance(new, dict):
            changes.extend(_diff_payload(old, new, path))
        elif old != new:
            changes.append({"field": path, "before": old, "after": new})
    return changes

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
        "canonical_key": canonical_identity_key(entity_type, normalized, fields=fields),
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
    """Persist observations using durable identity plus snapshot fingerprint."""
    items = list(items)
    if not items:
        return []

    fields = list(fields) if fields is not None else list(entity_type.fields.all())
    values_list = [_build_values(
        entity_type=entity_type,
        url=item["url"],
        payload=item["payload"],
        raw_capture=item.get("raw_capture"),
        evidence=item.get("evidence"),
        source_domain=item.get("source_domain"),
        fields=fields,
    ) for item in items]

    canonical_keys = {v["canonical_key"] for v in values_list if v["canonical_key"]}
    fingerprints = {v["fingerprint"] for v in values_list if not v["canonical_key"]}
    existing = {}
    if canonical_keys:
        existing.update({r.canonical_key: r for r in ExtractedRecord.objects.filter(entity_type=entity_type, canonical_key__in=canonical_keys)})
    if fingerprints:
        existing.update({r.fingerprint: r for r in ExtractedRecord.objects.filter(entity_type=entity_type, fingerprint__in=fingerprints)})

    identity_fields = [field for field in fields if field.is_identifier]
    unresolved = canonical_keys - set(existing)
    if unresolved and identity_fields:
        from django.db.models import Q
        identity_payloads = {}
        condition = Q()
        for values in values_list:
            key = values["canonical_key"]
            if not key or key in existing or key in identity_payloads:
                continue
            identity_payloads[key] = {field.slug: values["normalized_payload"].get(field.slug) for field in identity_fields}
            condition |= Q(normalized_payload__contains=identity_payloads[key])
        legacy_matches = {}
        duplicate_keys = set()
        if identity_payloads:
            qs = ExtractedRecord.objects.filter(entity_type=entity_type, canonical_key="").filter(condition).only("id", "entity_type_id", "canonical_key", "fingerprint", "status", "normalized_payload")
            for record in qs.iterator():
                for key, identity in identity_payloads.items():
                    if all(record.normalized_payload.get(field.slug) == identity[field.slug] for field in identity_fields):
                        if key in legacy_matches:
                            duplicate_keys.add(key)
                        else:
                            legacy_matches[key] = record
        for key in duplicate_keys:
            legacy_matches.pop(key, None)
        if legacy_matches:
            for key, record in legacy_matches.items():
                record.canonical_key = key
            ExtractedRecord.objects.bulk_update(legacy_matches.values(), ["canonical_key"], batch_size=max(1, int(batch_size)))
            existing.update(legacy_matches)

    missing = {}
    for values in values_list:
        key = values["canonical_key"] or values["fingerprint"]
        if key not in existing:
            missing.setdefault(key, values)
    if missing:
        ExtractedRecord.objects.bulk_create(
            [ExtractedRecord(entity_type=entity_type, **values) for values in missing.values()],
            batch_size=max(1, int(batch_size)),
            ignore_conflicts=True,
        )
        if canonical_keys:
            existing.update({r.canonical_key: r for r in ExtractedRecord.objects.filter(entity_type=entity_type, canonical_key__in=canonical_keys)})
        if fingerprints:
            existing.update({r.fingerprint: r for r in ExtractedRecord.objects.filter(entity_type=entity_type, fingerprint__in=fingerprints)})

    resolved = [existing[values["canonical_key"] or values["fingerprint"]] for values in values_list]

    # Resolve the latest persisted observation once per canonical record.
    previous_by_record = {}
    for record_id in {record.pk for record, values in zip(resolved, values_list) if values["raw_capture"] is not None}:
        previous_by_record[record_id] = (
            RecordObservation.objects.filter(record_id=record_id)
            .order_by("-observed_at", "-id")
            .first()
        )

    observations = []
    change_specs = []
    state_by_record = {}
    for record, values in zip(resolved, values_list):
        if values["raw_capture"] is None:
            continue
        previous = state_by_record.get(record.pk, previous_by_record.get(record.pk))
        observation = RecordObservation(
            record=record,
            raw_capture=values["raw_capture"],
            source_url=values["source_url"],
            source_domain=values["source_domain"],
            payload=values["payload"],
            normalized_payload=values["normalized_payload"],
            evidence=values["evidence"],
            fingerprint=values["fingerprint"],
        )
        observations.append(observation)
        if previous is not None and previous.fingerprint != values["fingerprint"]:
            changes = _diff_payload(previous.normalized_payload, values["normalized_payload"])
            if changes:
                change_specs.append((record, previous, observation, changes))
        state_by_record[record.pk] = observation

    if observations:
        RecordObservation.objects.bulk_create(
            observations,
            batch_size=max(1, int(batch_size)),
            ignore_conflicts=True,
        )
        persisted = RecordObservation.objects.filter(
            record_id__in={record.pk for record in resolved},
            raw_capture_id__in={item.raw_capture_id for item in observations},
        )
        persisted_map = {(item.record_id, item.raw_capture_id): item for item in persisted}
        changes = []
        for record, previous, pending, diff in change_specs:
            current = persisted_map.get((pending.record_id, pending.raw_capture_id))
            if current is None or current.fingerprint == previous.fingerprint:
                continue
            changes.append(RecordChange(
                record=record,
                previous_observation=previous,
                observation=current,
                changed_fields=[item["field"] for item in diff],
                before={item["field"]: item["before"] for item in diff},
                after={item["field"]: item["after"] for item in diff},
            ))
        if changes:
            RecordChange.objects.bulk_create(
                changes,
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
