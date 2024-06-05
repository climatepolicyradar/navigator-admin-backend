from fastapi import status
from fastapi.testclient import TestClient


def test_delete_when_ok(client: TestClient, document_service_mock, user_header_token):
    response = client.delete("/api/v1/documents/doc1", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    assert document_service_mock.delete.call_count == 1


def test_delete_when_not_found(
    client: TestClient, document_service_mock, user_header_token
):
    document_service_mock.missing = True
    response = client.delete("/api/v1/documents/doc1", headers=user_header_token)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Document not deleted: doc1"
    assert document_service_mock.delete.call_count == 1


def test_delete_fails_when_invalid_org(
    client: TestClient, document_service_mock, user_header_token
):
    document_service_mock.throw_validation_error = True
    response = client.delete("/api/v1/documents/doc1", headers=user_header_token)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "No org"
    assert document_service_mock.delete.call_count == 1


def test_delete_fails_when_org_mismatch(
    client: TestClient, document_service_mock, user_header_token
):
    document_service_mock.org_mismatch = True
    response = client.delete("/api/v1/documents/doc1", headers=user_header_token)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert data["detail"] == "Org mismatch"
    assert document_service_mock.delete.call_count == 1
