import pytest

from datahub.models import EntityType, ExtractedRecord, Location, MarketObservation, Pharmacy
from datahub.pharmacy_pipeline import upsert_pharmacy_from_record


@pytest.mark.django_db
def test_upsert_pharmacy_materializes_location_and_preserves_provenance():
    entity = EntityType.objects.create(name="داروخانه", slug="pharmacy-pipeline")
    record = ExtractedRecord.objects.create(
        entity_type=entity,
        source_url="https://pillix.ir/pharmacy/example",
        source_domain="pillix.ir",
        payload={
            "name": "داروخانه دکتر حسن",
            "province": "تهران",
            "city": "تهران",
            "district": "تهرانپارس",
            "address": "تهران، خیابان نمونه",
            "pharmacy_type": "شبانه‌روزی",
            "public_phone": "02112345678",
        },
        normalized_payload={
            "name": "داروخانه دکتر حسن",
            "province": "تهران",
            "city": "تهران",
            "district": "تهرانپارس",
            "address": "تهران، خیابان نمونه",
            "pharmacy_type": "شبانه‌روزی",
            "public_phone": "02112345678",
        },
        evidence=[{"field": "name", "selector": "h2", "value": "داروخانه دکتر حسن"}],
        fingerprint="a" * 64,
    )

    pharmacy = upsert_pharmacy_from_record(record)

    assert pharmacy.name == "داروخانه دکتر حسن"
    assert pharmacy.source_domain == "pillix.ir"
    assert pharmacy.source_url == record.source_url
    assert pharmacy.pharmacy_type == "شبانه‌روزی"
    assert pharmacy.location.province == "تهران"
    assert pharmacy.location.city == "تهران"
    assert pharmacy.location.district == "تهرانپارس"
    assert pharmacy.location.address == "تهران، خیابان نمونه"
    assert pharmacy.evidence == record.evidence
    assert MarketObservation.objects.count() == 0


@pytest.mark.django_db
def test_upsert_pharmacy_is_idempotent_for_same_source_url():
    entity = EntityType.objects.create(name="داروخانه", slug="pharmacy-idempotent")
    record = ExtractedRecord.objects.create(
        entity_type=entity,
        source_url="https://pillix.ir/pharmacy/example-2",
        source_domain="pillix.ir",
        payload={"name": "داروخانه الف", "province": "تهران", "city": "تهران"},
        normalized_payload={"name": "داروخانه الف", "province": "تهران", "city": "تهران"},
        fingerprint="b" * 64,
    )

    first = upsert_pharmacy_from_record(record)
    record.normalized_payload["pharmacy_type"] = "روزانه"
    record.evidence = [{"field": "pharmacy_type", "value": "روزانه"}]
    record.save(update_fields=["normalized_payload", "evidence"])
    second = upsert_pharmacy_from_record(record)

    assert first.pk == second.pk
    assert Pharmacy.objects.filter(
        source_domain="pillix.ir",
        source_url=record.source_url,
    ).count() == 1
    assert Location.objects.count() == 1
    assert second.pharmacy_type == "روزانه"
    assert second.evidence == record.evidence


@pytest.mark.django_db
def test_pharmacy_directory_page_can_materialize_multiple_pharmacies():
    entity = EntityType.objects.create(name="داروخانه", slug="pharmacy-directory-page")
    common = {
        "entity_type": entity,
        "source_url": "https://pillix.ir/pharmacy/county-tehran",
        "source_domain": "pillix.ir",
    }
    record_a = ExtractedRecord.objects.create(
        **common,
        payload={"name": "داروخانه الف", "province": "تهران", "city": "تهران", "address": "خیابان اول"},
        normalized_payload={"name": "داروخانه الف", "province": "تهران", "city": "تهران", "address": "خیابان اول"},
        fingerprint="c" * 64,
    )
    record_b = ExtractedRecord.objects.create(
        **common,
        payload={"name": "داروخانه ب", "province": "تهران", "city": "تهران", "address": "خیابان دوم"},
        normalized_payload={"name": "داروخانه ب", "province": "تهران", "city": "تهران", "address": "خیابان دوم"},
        fingerprint="d" * 64,
    )

    first = upsert_pharmacy_from_record(record_a)
    second = upsert_pharmacy_from_record(record_b)

    assert first.pk != second.pk
    assert Pharmacy.objects.filter(
        source_domain="pillix.ir",
        source_url=common["source_url"],
    ).count() == 2
