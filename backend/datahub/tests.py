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

@pytest.mark.django_db
def test_fingerprint_is_stable_across_persian_character_variants():
    from .pipeline import fingerprint

    first = fingerprint({"name": "كالا  ي", "city": "تهران"})
    second = fingerprint({"city": "تهران", "name": "کالا ی"})
    assert first == second


def test_similarity_is_symmetric_and_ignores_empty_matches():
    from .dedup import similarity
    from decimal import Decimal

    score_ab, fields_ab = similarity({"name": "کالا", "phone": ""}, {"name": "کالا", "phone": "1"})
    score_ba, fields_ba = similarity({"name": "کالا", "phone": "1"}, {"name": "کالا", "phone": ""})
    assert score_ab == score_ba == Decimal("0.5000")
    assert fields_ab == fields_ba == ["name"]

@pytest.mark.django_db
def test_records_api_filters_by_status_and_entity_type():
    from rest_framework.test import APIClient

    entity = EntityType.objects.create(name="داروخانه", slug="pharmacy")
    other = EntityType.objects.create(name="کلینیک", slug="clinic")
    process_record(entity_type=entity, url="https://example.com/a", payload={"name": "الف"})
    process_record(entity_type=other, url="https://example.com/b", payload={"name": "ب"})

    response = APIClient().get("/api/v1/records/", {"entity_type": entity.pk, "status": "parsed"})

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["entity_type"] == entity.pk
    assert response.data["results"][0]["status"] == "parsed"


@pytest.mark.django_db
def test_raw_capture_api_is_read_only_for_anonymous_users():
    from rest_framework.test import APIClient
    from .models import RawCapture

    capture = RawCapture.objects.create(url="https://example.com/raw", body="x")
    client = APIClient()

    response = client.get(f"/api/v1/raw/{capture.pk}/")
    assert response.status_code == 200

    delete_response = client.delete(f"/api/v1/raw/{capture.pk}/")
    assert delete_response.status_code == 403
    assert RawCapture.objects.filter(pk=capture.pk).exists()

@pytest.mark.django_db
def test_review_api_is_read_only_for_anonymous_users():
    from rest_framework.test import APIClient
    from .models import ReviewTask

    entity = EntityType.objects.create(name="پزشک", slug="doctor")
    record = process_record(entity_type=entity, url="https://example.com/doctor", payload={})
    client = APIClient()

    response = client.get("/api/v1/reviews/")
    assert response.status_code == 200

    post_response = client.post("/api/v1/reviews/", {"record": record.pk, "reason": "test"}, format="json")
    assert post_response.status_code == 403
    assert not ReviewTask.objects.filter(record=record).exists()


@pytest.mark.django_db
def test_audit_api_is_read_only_for_anonymous_users():
    from rest_framework.test import APIClient
    from .models import AuditEvent

    event = AuditEvent.objects.create(action="test", entity="ExtractedRecord", object_id="1")
    client = APIClient()

    response = client.get(f"/api/v1/audit/{event.pk}/")
    assert response.status_code == 200

    post_response = client.post("/api/v1/audit/", {"action": "forged"}, format="json")
    assert post_response.status_code == 403
    assert not AuditEvent.objects.filter(action="forged").exists()

@pytest.mark.django_db
def test_review_transition_updates_record_and_creates_audit_event():
    from django.contrib.auth import get_user_model
    from .models import AuditEvent, ReviewTask
    from .review import transition_review_task

    entity = EntityType.objects.create(name="داروخانه", slug="pharmacy-review")
    record = process_record(entity_type=entity, url="https://example.com/p", payload={"name": "الف"})
    task = ReviewTask.objects.create(record=record, reason="manual check")
    user = get_user_model().objects.create_user(username="reviewer")

    transition_review_task(task_id=task.pk, status=ReviewTask.Status.APPROVED, actor=user, notes="verified")

    task.refresh_from_db()
    record.refresh_from_db()
    event = AuditEvent.objects.get(action="review.transition", object_id=str(task.pk))
    assert task.status == ReviewTask.Status.APPROVED
    assert task.notes == "verified"
    assert record.status == ExtractedRecord.Status.APPROVED
    assert event.actor_id == user.pk
    assert event.before["review_status"] == ReviewTask.Status.OPEN
    assert event.after["record_status"] == ExtractedRecord.Status.APPROVED


@pytest.mark.django_db
def test_review_transition_rejects_invalid_repeat_transition():
    from .models import ReviewTask
    from .review import transition_review_task

    entity = EntityType.objects.create(name="کلینیک", slug="clinic-review")
    record = process_record(entity_type=entity, url="https://example.com/c", payload={"name": "الف"})
    task = ReviewTask.objects.create(record=record)
    transition_review_task(task_id=task.pk, status=ReviewTask.Status.REJECTED)

    with pytest.raises(ValueError, match="invalid transition"):
        transition_review_task(task_id=task.pk, status=ReviewTask.Status.APPROVED)
