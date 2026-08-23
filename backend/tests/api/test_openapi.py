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
    assert "/api/v1/workspaces/{workspace_id}/entities/tree" in document["paths"]
    assert "/api/v1/entities/{entity_id}" in document["paths"]
    assert "/api/v1/entities/{entity_id}/parent" in document["paths"]
    assert "/api/v1/workspaces/{workspace_id}/relationship-types" in document["paths"]
    assert "/api/v1/workspaces/{workspace_id}/relationships" in document["paths"]
    assert "/api/v1/entities/{entity_id}/relationships" in document["paths"]
    assert "/api/v1/relationships/{relationship_id}" in document["paths"]
    assert "/api/v1/workspaces/{workspace_id}/forms" in document["paths"]
    assert "/api/v1/forms/{form_id}" in document["paths"]
    assert "/api/v1/forms/{form_id}/fields" in document["paths"]
    assert "/api/v1/forms/{form_id}/publish" in document["paths"]
    assert "/api/v1/forms/{form_id}/new-version" in document["paths"]
    upload = document["paths"]["/api/v1/entities/{entity_id}/documents"]["post"]
    assert "multipart/form-data" in upload["requestBody"]["content"]
    assert "202" in upload["responses"]
    version_upload = document["paths"]["/api/v1/documents/{document_id}/versions"]["post"]
    assert "multipart/form-data" in version_upload["requestBody"]["content"]
    assert "202" in version_upload["responses"]
    download = document["paths"]["/api/v1/document-versions/{version_id}/download"]["get"]
    assert "200" in download["responses"]
    preview = document["paths"]["/api/v1/document-versions/{version_id}/preview"]["get"]
    assert {"200", "202"}.issubset(preview["responses"])
    assert "get" in document["paths"]["/api/v1/entities/{entity_id}/documents"]
    assert "get" in document["paths"]["/api/v1/documents/{document_id}"]
    assert "get" in document["paths"]["/api/v1/documents/{document_id}/versions"]
    assert "/api/v1/forms/{form_id}/render" in document["paths"]
    assert "/api/v1/forms/{form_id}/instances" in document["paths"]
    assert "/api/v1/form-instances/{instance_id}" in document["paths"]
