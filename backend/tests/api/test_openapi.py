"""Application and OpenAPI foundation tests."""

from fastapi.testclient import TestClient


def test_openapi_uses_version_31_and_exposes_health_routes(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    document = response.json()
    assert document["openapi"].startswith("3.1")
    assert "/health/live" in document["paths"]
    assert "/health/ready" in document["paths"]
