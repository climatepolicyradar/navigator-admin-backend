"""
Tests the routes for collection management.

This uses a service mock and ensures each endpoint calls into the service.
"""
from fastapi import status
from fastapi.testclient import TestClient
from app.model.collection import CollectionReadDTO

from unit_tests.helpers.collection import create_collection_dto


def test_get_all_collections_route_when_ok(
    client: TestClient, collection_service_mock, user_header_token
):
    response = client.get("/api/v1/collections", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert type(data) is list
    assert len(data) > 0
    assert data[0]["import_id"] == "test"
    assert collection_service_mock.all.call_count == 1


def test_get_collection_route_when_ok(
    client: TestClient, collection_service_mock, user_header_token
):
    response = client.get("/api/v1/collections/import_id", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "import_id"
    assert collection_service_mock.get.call_count == 1


def test_get_collection_route_when_not_found(
    client: TestClient, collection_service_mock, user_header_token
):
    collection_service_mock.missing = True
    response = client.get("/api/v1/collections/col1", headers=user_header_token)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Collection not found: col1"
    assert collection_service_mock.get.call_count == 1


def test_search_collection_route_when_ok(
    client: TestClient, collection_service_mock, user_header_token
):
    response = client.get("/api/v1/collections/?q=anything", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert type(data) is list
    assert len(data) > 0
    assert data[0]["import_id"] == "search1"
    assert collection_service_mock.search.call_count == 1


def test_search_collection_route_when_not_found(
    client: TestClient, collection_service_mock, user_header_token
):
    response = client.get("/api/v1/collections/?q=empty", headers=user_header_token)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Collections not found for term: empty"
    assert collection_service_mock.search.call_count == 1


def test_update_collection_route_when_ok(
    client: TestClient, collection_service_mock, user_header_token
):
    new_data = create_collection_dto("col1").dict()
    response = client.put(
        "/api/v1/collections", json=new_data, headers=user_header_token
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "col1"
    assert collection_service_mock.update.call_count == 1


def test_update_collection_route_when_not_found(
    client: TestClient, collection_service_mock, user_header_token
):
    collection_service_mock.missing = True
    new_data = create_collection_dto("col1").dict()
    response = client.put(
        "/api/v1/collections", json=new_data, headers=user_header_token
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Collection not updated: col1"
    assert collection_service_mock.update.call_count == 1


def test_create_collection_route_when_ok(
    client: TestClient, collection_service_mock, user_header_token
):
    new_data = create_collection_dto("col1").dict()
    response = client.post(
        "/api/v1/collections", json=new_data, headers=user_header_token
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["import_id"] == "col1"
    assert collection_service_mock.create.call_count == 1


def test_create_collection_route_when_not_found(
    client: TestClient, collection_service_mock, user_header_token
):
    collection_service_mock.missing = True
    new_data: CollectionReadDTO = create_collection_dto("col1")
    response = client.post(
        "/api/v1/collections", json=new_data.dict(), headers=user_header_token
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Collection not created: col1"
    assert collection_service_mock.create.call_count == 1


def test_delete_collection_route_when_ok(
    client: TestClient, collection_service_mock, admin_user_header_token
):
    response = client.delete(
        "/api/v1/collections/col1", headers=admin_user_header_token
    )
    assert response.status_code == status.HTTP_200_OK
    assert collection_service_mock.delete.call_count == 1


def test_delete_collection_fails_if_not_admin(
    client: TestClient, collection_service_mock, user_header_token
):
    response = client.delete("/api/v1/collections/col1", headers=user_header_token)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert collection_service_mock.delete.call_count == 0


def test_delete_collection_route_when_not_found(
    client: TestClient, collection_service_mock, admin_user_header_token
):
    collection_service_mock.missing = True
    response = client.delete(
        "/api/v1/collections/col1", headers=admin_user_header_token
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Collection not deleted: col1"
    assert collection_service_mock.delete.call_count == 1
