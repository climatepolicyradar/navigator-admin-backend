from fastapi import status
from fastapi.testclient import TestClient


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
