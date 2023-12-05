"""
Tests the routes for family management.

This uses a service mock and ensures each endpoint calls into the service.
"""
import logging

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from unit_tests.helpers.family import create_family_dto


def test_get_all_when_ok(client: TestClient, family_service_mock, user_header_token):
    response = client.get("/api/v1/families", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert type(data) is list
    assert len(data) > 0
    assert data[0]["import_id"] == "test"
    assert family_service_mock.all.call_count == 1


def test_get_when_ok(client: TestClient, family_service_mock, user_header_token):
    response = client.get("/api/v1/families/import_id", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "import_id"
    assert family_service_mock.get.call_count == 1


def test_get_when_not_found(client: TestClient, family_service_mock, user_header_token):
    family_service_mock.missing = True
    response = client.get("/api/v1/families/fam1", headers=user_header_token)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Family not found: fam1"
    assert family_service_mock.get.call_count == 1


def test_search_when_ok(client: TestClient, family_service_mock, user_header_token):
    response = client.get("/api/v1/families/?q=anything", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert type(data) is list
    assert len(data) > 0
    assert data[0]["import_id"] == "search1"
    assert family_service_mock.search.call_count == 1


def test_search_when_invalid_params(
    client: TestClient, family_service_mock, user_header_token
):
    response = client.get("/api/v1/families/?wrong=yes", headers=user_header_token)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "Search parameters are invalid: ['wrong']"
    assert family_service_mock.search.call_count == 0


def test_search_when_request_timeout(
    client: TestClient, family_service_mock, user_header_token, caplog
):
    family_service_mock.throw_timeout_error = True
    with caplog.at_level(logging.INFO):
        response = client.get("/api/v1/families/?q=timeout", headers=user_header_token)
    assert response.status_code == status.HTTP_408_REQUEST_TIMEOUT
    assert family_service_mock.search.call_count == 1
    assert (
        "Request timed out fetching matching families. Try adjusting your query."
        in caplog.text
    )


def test_search_when_not_found(
    client: TestClient, family_service_mock, user_header_token, caplog
):
    with caplog.at_level(logging.INFO):
        response = client.get("/api/v1/families/?q=empty", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    response.json()
    assert family_service_mock.search.call_count == 1
    assert (
        "Families not found for terms: {'q': 'empty', 'max_results': 500}"
        in caplog.text
    )


def test_update_when_ok(client: TestClient, family_service_mock, user_header_token):
    new_data = create_family_dto("fam1").model_dump()
    response = client.put(
        "/api/v1/families/fam1", json=new_data, headers=user_header_token
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "fam1"
    assert family_service_mock.update.call_count == 1


def test_update_when_not_found(
    client: TestClient, family_service_mock, user_header_token
):
    family_service_mock.missing = True
    new_data = create_family_dto("fam1").model_dump()
    response = client.put(
        "/api/v1/families/fam1", json=new_data, headers=user_header_token
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Family not updated: fam1"
    assert family_service_mock.update.call_count == 1


def test_create_when_ok(client: TestClient, family_service_mock, user_header_token):
    new_data = create_family_dto("fam1").model_dump()
    response = client.post("/api/v1/families", json=new_data, headers=user_header_token)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data == "new-import-id"
    assert family_service_mock.create.call_count == 1


def test_delete_when_ok(
    client: TestClient, family_service_mock, admin_user_header_token
):
    response = client.delete("/api/v1/families/fam1", headers=admin_user_header_token)
    assert response.status_code == status.HTTP_200_OK
    assert family_service_mock.delete.call_count == 1


@pytest.mark.skip(reason="No admin user for MVP")
def test_delete_fails_when_not_admin(
    client: TestClient, family_service_mock, user_header_token
):
    response = client.delete("/api/v1/families/fam1", headers=user_header_token)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert family_service_mock.delete.call_count == 0


def test_delete_when_not_found(
    client: TestClient, family_service_mock, admin_user_header_token
):
    family_service_mock.missing = True
    response = client.delete("/api/v1/families/fam1", headers=admin_user_header_token)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Family not deleted: fam1"
    assert family_service_mock.delete.call_count == 1
