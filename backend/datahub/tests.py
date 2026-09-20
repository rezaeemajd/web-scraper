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



@pytest.mark.django_db
def test_process_record_is_idempotent_for_same_normalized_fingerprint():
    entity = EntityType.objects.create(name="دارو تکراری", slug="drug-idempotent")
    first = process_record(
        entity_type=entity,
        url="https://example.com/a",
        payload={"name": " كالا "},
    )
    second = process_record(
        entity_type=entity,
        url="https://example.com/b",
        payload={"name": "کالا"},
    )

    assert first.pk == second.pk
    assert ExtractedRecord.objects.filter(entity_type=entity).count() == 1

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


@pytest.mark.django_db
def test_dedup_candidate_refreshes_existing_score_and_fields():
    from .models import DedupCandidate

    entity = EntityType.objects.create(name="دارو بروزرسانی", slug="drug-dedup-refresh")
    left = ExtractedRecord.objects.create(
        entity_type=entity, source_url="https://example.com/a",
        source_domain="example.com", payload={}, normalized_payload={"name": "A", "city": "X", "phone": "1"},
        fingerprint="a" * 64,
    )
    right = ExtractedRecord.objects.create(
        entity_type=entity, source_url="https://example.com/b",
        source_domain="example.com", payload={}, normalized_payload={"name": "A", "city": "X", "phone": "1", "email": "x@example.com"},
        fingerprint="b" * 64,
    )
    candidate = DedupCandidate.objects.create(
        record_a=left, record_b=right, similarity="0.7000", matched_fields=["old"]
    )

    candidates = find_candidates(right)
    candidate.refresh_from_db()

    assert candidates == [candidate]
    assert candidate.similarity == "0.7500"
    assert candidate.matched_fields == ["city", "name", "phone"]

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

@pytest.mark.django_db
def test_dedup_resolve_merge_archives_loser_and_audits():
    from django.contrib.auth import get_user_model
    from .dedup_review import resolve_dedup_candidate
    from .models import AuditEvent, DedupCandidate

    entity = EntityType.objects.create(name="پزشک", slug="doctor-dedup")
    left = ExtractedRecord.objects.create(entity_type=entity, source_url="https://example.com/a", source_domain="example.com", payload={}, normalized_payload={}, fingerprint="c" * 64)
    right = ExtractedRecord.objects.create(entity_type=entity, source_url="https://example.com/b", source_domain="example.com", payload={}, normalized_payload={}, fingerprint="d" * 64)
    candidate = DedupCandidate.objects.create(record_a=left, record_b=right, similarity="0.9000", matched_fields=["name"])
    user = get_user_model().objects.create_user(username="dedup-reviewer")

    resolve_dedup_candidate(candidate_id=candidate.pk, status=DedupCandidate.Status.MERGED, winner_id=left.pk, actor=user)

    candidate.refresh_from_db(); left.refresh_from_db(); right.refresh_from_db()
    event = AuditEvent.objects.get(action="dedup.resolve", object_id=str(candidate.pk))
    assert candidate.status == DedupCandidate.Status.MERGED
    assert left.status == ExtractedRecord.Status.RAW
    assert right.status == ExtractedRecord.Status.ARCHIVED
    assert event.metadata["winner_id"] == left.pk


@pytest.mark.django_db
def test_dedup_resolve_reject_does_not_archive_records():
    from .dedup_review import resolve_dedup_candidate
    from .models import DedupCandidate

    entity = EntityType.objects.create(name="دارو", slug="drug-dedup")
    left = ExtractedRecord.objects.create(entity_type=entity, source_url="https://example.com/a", source_domain="example.com", payload={}, normalized_payload={}, fingerprint="e" * 64)
    right = ExtractedRecord.objects.create(entity_type=entity, source_url="https://example.com/b", source_domain="example.com", payload={}, normalized_payload={}, fingerprint="f" * 64)
    candidate = DedupCandidate.objects.create(record_a=left, record_b=right, similarity="0.8000")

    resolve_dedup_candidate(candidate_id=candidate.pk, status=DedupCandidate.Status.REJECTED)

    left.refresh_from_db(); right.refresh_from_db()
    assert left.status == ExtractedRecord.Status.RAW
    assert right.status == ExtractedRecord.Status.RAW


@pytest.mark.django_db
def test_dedup_api_is_read_only_for_anonymous_users():
    from rest_framework.test import APIClient
    from .models import DedupCandidate

    entity = EntityType.objects.create(name="کلینیک", slug="clinic-dedup-api")
    left = ExtractedRecord.objects.create(entity_type=entity, source_url="https://example.com/a", source_domain="example.com", payload={}, normalized_payload={}, fingerprint="1" * 64)
    right = ExtractedRecord.objects.create(entity_type=entity, source_url="https://example.com/b", source_domain="example.com", payload={}, normalized_payload={}, fingerprint="2" * 64)
    candidate = DedupCandidate.objects.create(record_a=left, record_b=right, similarity="0.8000")
    response = APIClient().post(f"/api/v1/duplicates/{candidate.pk}/resolve/", {"status":"rejected"}, format="json")
    assert response.status_code == 403

@pytest.mark.django_db
def test_authenticated_users_cannot_mutate_workflow_status_directly():
    from django.contrib.auth import get_user_model
    from rest_framework.test import APIClient
    from .models import DedupCandidate, ReviewTask

    entity = EntityType.objects.create(name="آزمایشگاه", slug="lab-status")
    record = ExtractedRecord.objects.create(entity_type=entity, source_url="https://example.com/r", source_domain="example.com", payload={}, normalized_payload={}, fingerprint="9" * 64)
    task = ReviewTask.objects.create(record=record)
    other = ExtractedRecord.objects.create(entity_type=entity, source_url="https://example.com/s", source_domain="example.com", payload={}, normalized_payload={}, fingerprint="8" * 64)
    candidate = DedupCandidate.objects.create(record_a=record, record_b=other, similarity="0.8000")
    user = get_user_model().objects.create_user(username="api-user", is_staff=True)
    client = APIClient(); client.force_authenticate(user=user)

    record_response = client.patch(f"/api/v1/records/{record.pk}/", {"status": "approved"}, format="json")
    review_response = client.patch(f"/api/v1/reviews/{task.pk}/", {"status": "approved"}, format="json")
    dedup_response = client.patch(f"/api/v1/duplicates/{candidate.pk}/", {"status": "merged"}, format="json")

    assert record_response.status_code == 400
    assert review_response.status_code == 400
    assert dedup_response.status_code == 400


@pytest.mark.django_db
def test_dedup_blocks_candidates_using_searchable_fields():
    entity = EntityType.objects.create(name="پزشک بلاک", slug="doctor-blocking")
    EntityField.objects.create(
        entity_type=entity, name="نام", slug="name", searchable=True
    )
    EntityField.objects.create(
        entity_type=entity, name="تلفن", slug="phone", searchable=True
    )
    target = ExtractedRecord.objects.create(
        entity_type=entity,
        source_url="https://example.com/target",
        source_domain="example.com",
        payload={},
        normalized_payload={"name": "A", "phone": "123"},
        fingerprint="1" * 64,
    )
    match = ExtractedRecord.objects.create(
        entity_type=entity,
        source_url="https://example.com/match",
        source_domain="example.com",
        payload={},
        normalized_payload={"name": "A", "phone": "123", "city": "X"},
        fingerprint="2" * 64,
    )
    unrelated = ExtractedRecord.objects.create(
        entity_type=entity,
        source_url="https://example.com/unrelated",
        source_domain="example.com",
        payload={},
        normalized_payload={"name": "Z", "phone": "999", "city": "Y"},
        fingerprint="3" * 64,
    )
    candidates = find_candidates(target)
    assert [item.record_b_id for item in candidates] == [match.pk]
    assert unrelated.pk not in {item.record_a_id for item in candidates}


@pytest.mark.django_db
def test_raw_capture_list_omits_large_body_and_headers():
    from .models import RawCapture
    from rest_framework.test import APIClient

    capture = RawCapture.objects.create(
        url="https://example.com/large",
        body="x" * 10000,
        headers={"content-type": "text/html"},
    )
    response = APIClient().get("/api/v1/raw/")
    assert response.status_code == 200
    item = next(row for row in response.data["results"] if row["id"] == capture.pk)
    assert "body" not in item
    assert "headers" not in item

    detail = APIClient().get(f"/api/v1/raw/{capture.pk}/")
    assert detail.status_code == 200
    assert detail.data["body"] == "x" * 10000
    assert detail.data["headers"]["content-type"] == "text/html"


@pytest.mark.django_db
def test_record_list_omits_large_json_and_detail_keeps_it():
    from rest_framework.test import APIClient

    entity = EntityType.objects.create(name="رکورد سبک", slug="record-list-light")
    record = ExtractedRecord.objects.create(
        entity_type=entity,
        source_url="https://example.com/record",
        source_domain="example.com",
        payload={"name": "A", "html": "x" * 5000},
        normalized_payload={"name": "A"},
        evidence=[{"field": "name", "value": "A"}],
        validation_errors=[{"field": "x", "code": "required"}],
        fingerprint="7" * 64,
    )

    client = APIClient()
    response = client.get("/api/v1/records/")
    assert response.status_code == 200
    item = next(row for row in response.data["results"] if row["id"] == record.pk)
    assert "payload" not in item
    assert "normalized_payload" not in item
    assert "evidence" not in item
    assert "validation_errors" not in item

    detail = client.get(f"/api/v1/records/{record.pk}/")
    assert detail.status_code == 200
    assert detail.data["payload"]["html"] == "x" * 5000
    assert detail.data["normalized_payload"]["name"] == "A"


@pytest.mark.django_db
def test_dedup_persists_multiple_candidates_in_bulk_and_refreshes_them():
    from .models import DedupCandidate

    entity = EntityType.objects.create(name="پزشک چندتایی", slug="doctor-bulk-dedup")
    EntityField.objects.create(entity_type=entity, name="نام", slug="name", searchable=True)
    target = ExtractedRecord.objects.create(
        entity_type=entity,
        source_url="https://example.com/target",
        source_domain="example.com",
        normalized_payload={"name": "A", "city": "X"},
        fingerprint="a" * 64,
    )
    others = []
    for index in range(3):
        others.append(
            ExtractedRecord.objects.create(
                entity_type=entity,
                source_url=f"https://example.com/{index}",
                source_domain="example.com",
                normalized_payload={"name": "A", "city": "X"},
                fingerprint=str(index + 1) * 64,
            )
        )

    first = find_candidates(target, limit=3)
    assert len(first) == 3
    assert DedupCandidate.objects.filter(
        record_a=target
    ).count() == 3

    for candidate in first:
        candidate.matched_fields = ["stale"]
        candidate.similarity = "0.7000"
        candidate.save(update_fields=["matched_fields", "similarity"])

    second = find_candidates(target, limit=3)
    assert len(second) == 3
    assert all(candidate.matched_fields == ["city", "name"] for candidate in second)
    assert all(candidate.similarity == "1.0000" for candidate in second)
