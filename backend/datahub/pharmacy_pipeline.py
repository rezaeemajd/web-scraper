import hashlib

from django.db import transaction

from .models import ExtractedRecord, Location, Pharmacy
from .pipeline import normalize_text


_PHARMACY_FIELDS = (
    "name",
    "province",
    "city",
    "district",
    "address",
    "pharmacy_type",
    "service_hours",
    "public_phone",
    "website",
)


def _text(value):
    return normalize_text(value or "").strip() if isinstance(value, str) else ""


def _location_values(payload):
    province = _text(payload.get("province"))
    city = _text(payload.get("city"))
    district = _text(payload.get("district"))
    address = _text(payload.get("address"))
    normalized_address = address

    return {
        "country": "ایران",
        "province": province,
        "city": city,
        "district": district,
        "address": address,
        "normalized_address": normalized_address,
    }


def _pharmacy_key(source_domain, payload):
    identity = "|".join(
        [
            _text(source_domain).lower(),
            _text(payload.get("name")),
            _text(payload.get("province")),
            _text(payload.get("city")),
            _text(payload.get("district")),
            _text(payload.get("address")),
        ]
    )
    return "pharm:v1:" + hashlib.sha256(identity.encode("utf-8")).hexdigest()


@transaction.atomic
def upsert_pharmacy_from_record(record: ExtractedRecord):
    """Materialize one parsed pharmacy record without inventing product availability."""
    payload = record.normalized_payload or record.payload or {}
    name = _text(payload.get("name") or payload.get("pharmacy_name"))
    if not name:
        raise ValueError("pharmacy record requires name")

    location_values = _location_values(payload)
    location = (
        Location.objects.filter(**location_values)
        .order_by("id")
        .first()
    )
    if location is None:
        location = Location.objects.create(**location_values)

    values = {
        "name": name,
        "location": location,
        "source_url": record.source_url,
        "source_domain": record.source_domain,
        "canonical_key": _pharmacy_key(record.source_domain, payload),
        "pharmacy_type": _text(payload.get("pharmacy_type")),
        "service_hours": _text(payload.get("service_hours")),
        "public_phone": _text(payload.get("public_phone")),
        "website": _text(payload.get("website")),
        "evidence": record.evidence or [],
        "active": True,
    }

    pharmacy, _ = Pharmacy.objects.update_or_create(
        source_domain=record.source_domain,
        source_url=record.source_url,
        defaults=values,
    )
    return pharmacy
