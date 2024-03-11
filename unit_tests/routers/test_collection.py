"""
Tests the routes for collection management.

This uses a service mock and ensures each endpoint calls into the service.
"""

import logging

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from unit_tests.helpers.collection import (
    create_collection_write_dto,
)


def test_get_all_when_ok(
    client: TestClient, collection_service_mock, user_header_token
):
    response = client.get("/api/v1/collections", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert type(data) is list
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


def test_search_when_ok(client: TestClient, collection_service_mock, user_header_token):
    response = client.get("/api/v1/collections/?q=anything", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert type(data) is list
    assert len(data) > 0
    assert data[0]["import_id"] == "search1"
    assert collection_service_mock.search.call_count == 1


def test_search_when_invalid_params(
    client: TestClient, collection_service_mock, user_header_token
):
    response = client.get("/api/v1/collections/?wrong=yes", headers=user_header_token)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "Search parameters are invalid: ['wrong']"
    assert collection_service_mock.search.call_count == 0


def test_search_when_db_error(
    client: TestClient, collection_service_mock, user_header_token
):
    collection_service_mock.throw_repository_error = True
    response = client.get("/api/v1/collections/?q=error", headers=user_header_token)
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "bad repo"
    assert collection_service_mock.search.call_count == 1


def test_search_when_request_timeout(
    client: TestClient,
    collection_service_mock,
    user_header_token,
    caplog,
):
    collection_service_mock.throw_timeout_error = True
    with caplog.at_level(logging.INFO):
        response = client.get(
            "/api/v1/collections/?q=timeout", headers=user_header_token
        )
    assert response.status_code == status.HTTP_408_REQUEST_TIMEOUT
    assert collection_service_mock.search.call_count == 1
    assert (
        "Request timed out fetching matching collections. Try adjusting your query."
        in caplog.text
    )


def test_search_when_not_found(
    client: TestClient, collection_service_mock, user_header_token, caplog
):
    collection_service_mock.missing = True
    with caplog.at_level(logging.INFO):
        response = client.get("/api/v1/collections/?q=stuff", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    response.json()
    assert collection_service_mock.search.call_count == 1
    assert (
        "Collections not found for terms: {'q': 'stuff', 'max_results': 500}"
        in caplog.text
    )


def test_update_when_ok(client: TestClient, collection_service_mock, user_header_token):
    new_data = create_collection_write_dto().model_dump()
    response = client.put(
        "/api/v1/collections/col1", json=new_data, headers=user_header_token
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "col1"
    assert collection_service_mock.update.call_count == 1


def test_update_when_not_found(
    client: TestClient, collection_service_mock, user_header_token
):
    collection_service_mock.missing = True
    new_data = create_collection_write_dto().model_dump()
    response = client.put(
        "/api/v1/collections/col1", json=new_data, headers=user_header_token
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Collection not updated: col1"
    assert collection_service_mock.update.call_count == 1


def test_create_when_ok(client: TestClient, collection_service_mock, user_header_token):
    new_data = create_collection_write_dto().model_dump()
    response = client.post(
        "/api/v1/collections", json=new_data, headers=user_header_token
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data == "test.new.collection.0"
    assert collection_service_mock.create.call_count == 1


def test_delete_when_ok(
    client: TestClient, collection_service_mock, admin_user_header_token
):
    response = client.delete(
        "/api/v1/collections/col1", headers=admin_user_header_token
    )
    assert response.status_code == status.HTTP_200_OK
    assert collection_service_mock.delete.call_count == 1


@pytest.mark.skip(reason="No admin user for MVP")
def test_delete_collection_fails_if_not_admin(
    client: TestClient, collection_service_mock, user_header_token
):
    response = client.delete("/api/v1/collections/col1", headers=user_header_token)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert collection_service_mock.delete.call_count == 0


def test_delete_when_not_found(
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
