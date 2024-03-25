import logging

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from tests.unit_tests.helpers.document import (
    create_document_create_dto,
    create_document_write_dto,
)


def test_get_all_when_ok(client: TestClient, user_header_token, document_service_mock):
    response = client.get("/api/v1/documents", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["import_id"] == "test"
    assert document_service_mock.all.call_count == 1


def test_get_when_ok(client: TestClient, document_service_mock, user_header_token):
    response = client.get("/api/v1/documents/import_id", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "import_id"
    assert document_service_mock.get.call_count == 1


def test_get_when_not_found(
    client: TestClient, document_service_mock, user_header_token
):
    document_service_mock.missing = True
    response = client.get("/api/v1/documents/doc1", headers=user_header_token)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Document not found: doc1"
    assert document_service_mock.get.call_count == 1


def test_search_when_ok(client: TestClient, document_service_mock, user_header_token):
    response = client.get("/api/v1/documents/?q=anything", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["import_id"] == "search1"
    assert document_service_mock.search.call_count == 1


def test_search_when_invalid_params(
    client: TestClient, document_service_mock, user_header_token
):
    response = client.get("/api/v1/documents/?wrong=yes", headers=user_header_token)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "Search parameters are invalid: ['wrong']"
    assert document_service_mock.search.call_count == 0


def test_search_when_db_error(
    client: TestClient, document_service_mock, user_header_token
):
    document_service_mock.throw_repository_error = True
    response = client.get("/api/v1/documents/?q=error", headers=user_header_token)
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "bad repo"
    assert document_service_mock.search.call_count == 1


def test_search_when_request_timeout(
    client: TestClient, document_service_mock, user_header_token, caplog
):
    document_service_mock.throw_timeout_error = True
    with caplog.at_level(logging.INFO):
        response = client.get("/api/v1/documents/?q=timeout", headers=user_header_token)
    assert response.status_code == status.HTTP_408_REQUEST_TIMEOUT
    assert document_service_mock.search.call_count == 1
    assert (
        "Request timed out fetching matching documents. Try adjusting your query."
        in caplog.text
    )


def test_search_when_not_found(
    client: TestClient, document_service_mock, user_header_token, caplog
):
    document_service_mock.missing = True
    with caplog.at_level(logging.INFO):
        response = client.get("/api/v1/documents/?q=stuff", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    response.json()
    assert document_service_mock.search.call_count == 1
    assert (
        "Documents not found for terms: {'q': 'stuff', 'max_results': 500}"
        in caplog.text
    )


def test_update_when_ok(client: TestClient, document_service_mock, user_header_token):
    new_data = create_document_write_dto("doc1").model_dump(mode="json")
    response = client.put(
        "/api/v1/documents/D.0.0.1", json=new_data, headers=user_header_token
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "D.0.0.1"
    assert document_service_mock.update.call_count == 1


def test_update_when_not_found(
    client: TestClient, document_service_mock, user_header_token
):
    document_service_mock.missing = True
    new_data = create_document_write_dto("doc1").model_dump(mode="json")
    response = client.put(
        "/api/v1/documents/a.b.c.d", json=new_data, headers=user_header_token
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Document not updated: a.b.c.d"
    assert document_service_mock.update.call_count == 1


def test_update_when_validation_error(
    client: TestClient, document_service_mock, user_header_token
):
    document_service_mock.throw_validation_error = True
    new_data = create_document_write_dto("doc1").model_dump(mode="json")
    response = client.put(
        "/api/v1/documents/a.b.c.d", json=new_data, headers=user_header_token
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "Variant name is empty"
    assert document_service_mock.update.call_count == 1


def test_create_when_ok(client: TestClient, document_service_mock, user_header_token):
    new_data = create_document_create_dto("doc1").model_dump(mode="json")
    response = client.post(
        "/api/v1/documents", json=new_data, headers=user_header_token
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data == "new.doc.id.0"
    assert document_service_mock.create.call_count == 1


def test_create_when_family_not_found(
    client: TestClient, document_service_mock, user_header_token
):
    document_service_mock.missing = True
    new_data = create_document_create_dto("this_family")
    response = client.post(
        "/api/v1/documents",
        json=new_data.model_dump(mode="json"),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "Could not find family for this_family"
    assert document_service_mock.create.call_count == 1


def test_delete_when_ok(
    client: TestClient, document_service_mock, admin_user_header_token
):
    response = client.delete("/api/v1/documents/doc1", headers=admin_user_header_token)
    assert response.status_code == status.HTTP_200_OK
    assert document_service_mock.delete.call_count == 1


@pytest.mark.skip(reason="No admin user for MVP")
def test_delete_document_fails_if_not_admin(
    client: TestClient, document_service_mock, user_header_token
):
    response = client.delete("/api/v1/documents/doc1", headers=user_header_token)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert document_service_mock.delete.call_count == 0


def test_delete_when_not_found(
    client: TestClient, document_service_mock, admin_user_header_token
):
    document_service_mock.missing = True
    response = client.delete("/api/v1/documents/doc1", headers=admin_user_header_token)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Document not deleted: doc1"
    assert document_service_mock.delete.call_count == 1
