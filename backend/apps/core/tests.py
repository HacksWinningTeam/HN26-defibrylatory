"""Tests for core API endpoints and OpenAPI schema generation."""

from unittest.mock import MagicMock

import pytest
from django.contrib.auth import get_user_model
from django.db import DatabaseError
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework.views import APIView


class _EchoCreateView(APIView):
    """Minimal unsafe-method view that relies on the global DRF authentication defaults."""

    def post(self, request: Request) -> Response:
        return Response({"ok": True}, status=status.HTTP_201_CREATED)


@pytest.mark.django_db
def test_post_without_csrf_token_succeeds_for_admin_logged_in_browser() -> None:
    """A same-origin admin session must not make API POSTs fail with 403 CSRF Failed."""
    user = get_user_model().objects.create_superuser("admin", "admin@example.com", "pw")
    factory = APIRequestFactory(enforce_csrf_checks=True)
    request = factory.post("/api/echo/", {"name": "demo"}, format="json")
    request.user = user  # what AuthenticationMiddleware sets for a logged-in admin session

    response = _EchoCreateView.as_view()(request)

    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_health_check_returns_ok() -> None:
    client = APIClient()
    response = client.get("/api/health/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database"] == "ok"
    assert "timestamp" in payload


@pytest.mark.django_db
def test_health_check_returns_503_when_database_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_cursor = MagicMock(side_effect=DatabaseError("database unavailable"))
    monkeypatch.setattr("apps.core.views.connection.cursor", mock_cursor)

    client = APIClient()
    response = client.get("/api/health/")

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["database"] == "error"
    assert "timestamp" in payload


@pytest.mark.django_db
def test_openapi_schema_includes_health_endpoint() -> None:
    client = APIClient()
    response = client.get("/api/schema/", HTTP_ACCEPT="application/json")

    assert response.status_code == 200
    schema = response.json()
    assert "/api/health/" in schema["paths"]


@pytest.mark.django_db
def test_api_docs_and_redoc_render() -> None:
    client = APIClient()

    docs_response = client.get("/api/docs/")
    redoc_response = client.get("/api/redoc/")

    assert docs_response.status_code == 200
    assert redoc_response.status_code == 200
