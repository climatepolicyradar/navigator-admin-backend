import pytest
from fastapi import status
from fastapi.testclient import TestClient


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
