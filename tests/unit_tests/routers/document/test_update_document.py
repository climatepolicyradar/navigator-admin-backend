from fastapi import status
from fastapi.testclient import TestClient

from tests.helpers.document import create_document_write_dto


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
    assert data["detail"] == "Validation error"
    assert document_service_mock.update.call_count == 1
