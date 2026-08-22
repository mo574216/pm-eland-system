"""Application and OpenAPI foundation tests."""

from fastapi.testclient import TestClient


def test_openapi_uses_version_31_and_exposes_health_routes(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    document = response.json()
    assert document["openapi"].startswith("3.1")
    assert "/health/live" in document["paths"]
    assert "/health/ready" in document["paths"]
    assert "/api/v1/workspaces" in document["paths"]
    assert "/api/v1/workspaces/{workspace_id}" in document["paths"]
    assert "/api/v1/workspaces/{workspace_id}/members" in document["paths"]
    assert "/api/v1/workspaces/{workspace_id}/members/{user_id}" in document["paths"]
    assert "/api/v1/workspaces/{workspace_id}/entity-types" in document["paths"]
    assert "/api/v1/entity-types/{entity_type_id}" in document["paths"]
    assert "/api/v1/entity-types/{entity_type_id}/attributes" in document["paths"]
    assert "/api/v1/attributes/{attribute_id}" in document["paths"]
    assert "/api/v1/workspaces/{workspace_id}/entities" in document["paths"]
    assert "/api/v1/entities/{entity_id}" in document["paths"]
