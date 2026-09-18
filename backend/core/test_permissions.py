import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from sources.models import Source


@pytest.mark.django_db
def test_anonymous_can_read_sources_but_cannot_mutate():
    source = Source.objects.create(
        name="Public Source",
        domain="example.com",
        base_url="https://example.com",
    )
    client = APIClient()

    response = client.get("/api/v1/sources/")
    assert response.status_code == 200

    response = client.patch(
        f"/api/v1/sources/{source.pk}/",
        {"name": "Changed"},
        format="json",
    )
    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_authenticated_non_staff_cannot_mutate_sources():
    user = get_user_model().objects.create_user(
        username="collector",
        password="test-password",
        is_staff=False,
    )
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(
        "/api/v1/sources/",
        {
            "name": "Blocked Source",
            "domain": "example.com",
            "base_url": "https://example.com",
        },
        format="json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_staff_can_create_source():
    user = get_user_model().objects.create_user(
        username="admin",
        password="test-password",
        is_staff=True,
    )
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(
        "/api/v1/sources/",
        {
            "name": "Staff Source",
            "domain": "example.com",
            "base_url": "https://example.com",
        },
        format="json",
    )
    assert response.status_code == 201
