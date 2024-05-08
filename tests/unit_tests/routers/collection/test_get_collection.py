"""
Tests the routes for collection management.

This uses a service mock and ensures each endpoint calls into the service.
"""

from fastapi import status
from fastapi.testclient import TestClient


def test_get_all_when_ok(
    client: TestClient, collection_service_mock, user_header_token
):
    response = client.get("/api/v1/collections", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["import_id"] == "test"
    assert collection_service_mock.all.call_count == 1


def test_get_when_ok(client: TestClient, collection_service_mock, user_header_token):
    response = client.get("/api/v1/collections/import_id", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "import_id"
    assert collection_service_mock.get.call_count == 1


def test_get_when_not_found(
    client: TestClient, collection_service_mock, user_header_token
):
    collection_service_mock.missing = True
    response = client.get("/api/v1/collections/col1", headers=user_header_token)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Collection not found: col1"
    assert collection_service_mock.get.call_count == 1
