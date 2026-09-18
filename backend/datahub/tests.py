import pytest
from .models import EntityField, EntityType, ExtractedRecord
from .dedup import find_candidates
from .pipeline import canonical_url, normalize_value, process_record


@pytest.mark.django_db
def test_pipeline_normalizes_and_scores_required_fields():
    entity = EntityType.objects.create(name="دارو", slug="drug")
    EntityField.objects.create(entity_type=entity, name="نام", slug="name", required=True)
    EntityField.objects.create(entity_type=entity, name="برند", slug="brand", required=False)
    record = process_record(
        entity_type=entity,
        url="HTTPS://Example.COM/path/",
        payload={"name": " كالا  ", "brand": "ب رند"},
    )
    assert record.source_url == "https://example.com/path"
    assert record.normalized_payload["name"] == "کالا"
    assert record.quality_score == 1
    assert record.validation_errors == []


@pytest.mark.django_db
def test_pipeline_marks_missing_required_field_for_review():
    entity = EntityType.objects.create(name="کلینیک", slug="clinic")
    EntityField.objects.create(entity_type=entity, name="نام", slug="name", required=True)
    record = process_record(entity_type=entity, url="https://example.com/clinic", payload={})
    assert record.status == ExtractedRecord.Status.REVIEW
    assert record.validation_errors == [{"field": "name", "code": "required"}]
    assert record.quality_score == 0


@pytest.mark.django_db
def test_dedup_candidate_is_created_for_high_similarity():
    entity = EntityType.objects.create(name="دارو", slug="drug")
    left = ExtractedRecord.objects.create(
        entity_type=entity,
        source_url="https://example.com/a",
        source_domain="example.com",
        payload={"name": "A", "city": "Tehran"},
        normalized_payload={"name": "A", "city": "Tehran"},
        fingerprint="a" * 64,
    )
    right = ExtractedRecord.objects.create(
        entity_type=entity,
        source_url="https://example.com/b",
        source_domain="example.com",
        payload={"name": "A", "city": "Tehran", "phone": "1"},
        normalized_payload={"name": "A", "city": "Tehran", "phone": "1"},
        fingerprint="b" * 64,
    )
    candidates = find_candidates(right)
    assert len(candidates) == 1
    assert candidates[0].record_a_id == left.pk
    assert candidates[0].record_b_id == right.pk
    assert set(candidates[0].matched_fields) == {"city", "name"}


def test_canonical_url():
    assert canonical_url("HTTPS://Example.COM/a///?x=1") == "https://example.com/a?x=1"


def test_recursive_normalization():
    assert normalize_value({"x": [" ي ", {"y": "ك"}]}) == {"x": ["ی", {"y": "ک"}]}
