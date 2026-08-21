"""Health endpoint contract tests."""

from typing import Protocol, cast
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


class AccessLogRecord(Protocol):
    request_id: str
    method: str
    path: str
    status_code: int
    duration_ms: float


def test_liveness_uses_standard_envelope_and_request_id(client: TestClient) -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "data": {"status": "ok"},
        "error": None,
        "meta": {},
    }
    UUID(response.headers["X-Request-ID"])
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_valid_client_request_id_is_propagated(client: TestClient) -> None:
    request_id = str(uuid4())
    response = client.get("/health/live", headers={"X-Request-ID": request_id})
    assert response.headers["X-Request-ID"] == request_id


def test_invalid_client_request_id_is_replaced(client: TestClient) -> None:
    response = client.get("/health/live", headers={"X-Request-ID": "not-a-uuid"})
    assert response.headers["X-Request-ID"] != "not-a-uuid"
    UUID(response.headers["X-Request-ID"])


def test_request_completion_log_contains_correlation_fields(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level("INFO", logger="app.access")

    response = client.get("/health/live")

    record = cast(
        AccessLogRecord,
        next(record for record in caplog.records if record.message == "request_completed"),
    )
    assert record.request_id == response.headers["X-Request-ID"]
    assert record.method == "GET"
    assert record.path == "/health/live"
    assert record.status_code == 200
    assert record.duration_ms >= 0


def test_readiness_succeeds_when_database_is_not_configured(client: TestClient) -> None:
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["data"] == {
        "status": "ready",
        "checks": {"database": "not_configured"},
    }


def test_readiness_fails_closed_without_database_probe() -> None:
    async def database_is_unavailable() -> bool:
        return False

    application = create_app(
        Settings(database_url="postgresql://configured"),
        database_probe=database_is_unavailable,
    )
    with TestClient(application) as client:
        response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["error"] == {
        "code": "DEPENDENCY_UNAVAILABLE",
        "message": "A required service is unavailable.",
        "details": {"checks": {"database": "unavailable"}},
    }


def test_readiness_uses_configured_database_probe() -> None:
    async def database_is_ready() -> bool:
        return True

    application: FastAPI = create_app(
        Settings(database_url="postgresql://configured"), database_probe=database_is_ready
    )
    with TestClient(application) as client:
        response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["data"]["checks"] == {"database": "ok"}
