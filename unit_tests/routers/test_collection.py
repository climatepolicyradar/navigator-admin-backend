"""
Tests the routes for collection management.

This uses a service mock and ensures each endpoint calls into the service.
"""
from fastapi import status
from fastapi.testclient import TestClient
from app.model.collection import CollectionDTO

from unit_tests.helpers.collection import create_collection_dto


def test_get_all_collection_uses_service_200(
    client: TestClient, collection_service_mock, user_header_token
):
    response = client.get("/api/v1/collections", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert type(data) is list
    assert len(data) > 0
    assert data[0]["import_id"] == "test"
    assert collection_service_mock.all.call_count == 1


def test_get_collection_uses_service_200(
    client: TestClient, collection_service_mock, user_header_token
):
    response = client.get("/api/v1/collections/import_id", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "import_id"
    assert collection_service_mock.get.call_count == 1


def test_get_collection_uses_service_404(
    client: TestClient, collection_service_mock, user_header_token
):
    response = client.get("/api/v1/collections/missing", headers=user_header_token)
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Collection not found: missing"
    assert collection_service_mock.get.call_count == 1


def test_search_collection_uses_service_200(
    client: TestClient, collection_service_mock, user_header_token
):
    response = client.get("/api/v1/collections/?q=anything", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert type(data) is list
    assert len(data) > 0
    assert data[0]["import_id"] == "search1"
    assert collection_service_mock.search.call_count == 1


def test_search_collection_uses_service_404(
    client: TestClient, collection_service_mock, user_header_token
):
    response = client.get("/api/v1/collections/?q=empty", headers=user_header_token)
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "collections not found for term: empty"
    assert collection_service_mock.search.call_count == 1


def test_update_collection_uses_service_200(
    client: TestClient, collection_service_mock, user_header_token
):
    new_data = create_collection_dto("fam1").dict()
    response = client.put(
        "/api/v1/collections", json=new_data, headers=user_header_token
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "fam1"
    assert collection_service_mock.update.call_count == 1


def test_update_collection_uses_service_404(
    client: TestClient, collection_service_mock, user_header_token
):
    new_data = create_collection_dto("missing").dict()
    response = client.put(
        "/api/v1/collections", json=new_data, headers=user_header_token
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Collection not updated: missing"
    assert collection_service_mock.update.call_count == 1


def test_create_collection_uses_service_200(
    client: TestClient, collection_service_mock, user_header_token
):
    new_data = create_collection_dto("fam1").dict()
    response = client.post(
        "/api/v1/collections", json=new_data, headers=user_header_token
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["import_id"] == "fam1"
    assert collection_service_mock.create.call_count == 1


def test_create_collection_uses_service_404(
    client: TestClient, collection_service_mock, user_header_token
):
    new_data: CollectionDTO = create_collection_dto("fam1")
    new_data.import_id = "missing"
    response = client.post(
        "/api/v1/collections", json=new_data.dict(), headers=user_header_token
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Collection not created: missing"
    assert collection_service_mock.create.call_count == 1


def test_delete_collection_uses_service_200(
    client: TestClient, collection_service_mock, admin_user_header_token
):
    response = client.delete(
        "/api/v1/collections/fam1", headers=admin_user_header_token
    )
    assert response.status_code == status.HTTP_200_OK
    assert collection_service_mock.delete.call_count == 1


def test_delete_collection_fails_if_not_admin(
    client: TestClient, collection_service_mock, user_header_token
):
    response = client.delete("/api/v1/collections/fam1", headers=user_header_token)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert collection_service_mock.delete.call_count == 0


def test_delete_collection_uses_service_404(
    client: TestClient, collection_service_mock, admin_user_header_token
):
    response = client.delete(
        "/api/v1/collections/missing", headers=admin_user_header_token
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Collection not deleted: missing"
    assert collection_service_mock.delete.call_count == 1
