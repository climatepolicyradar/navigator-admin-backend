from fastapi import status
from fastapi.testclient import TestClient

from tests.helpers.document import create_document_create_dto


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
