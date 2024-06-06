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


def test_create_fails_when_validation_error(
    client: TestClient, document_service_mock, user_header_token
):
    document_service_mock.throw_validation_error = True
    new_data = create_document_create_dto("validation_error").model_dump(mode="json")
    response = client.post(
        "/api/v1/documents", json=new_data, headers=user_header_token
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "Validation error"
    assert document_service_mock.delete.call_count == 0


def test_create_fails_when_org_mismatch(
    client: TestClient, document_service_mock, user_header_token
):
    document_service_mock.org_mismatch = True
    new_data = create_document_create_dto("unfccc_fam").model_dump(mode="json")
    response = client.post(
        "/api/v1/documents", json=new_data, headers=user_header_token
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert data["detail"] == "Org mismatch"
    assert document_service_mock.delete.call_count == 0


def test_create_success_when_org_mismatch_super(
    client: TestClient, document_service_mock, superuser_header_token
):
    document_service_mock.org_mismatch = True
    document_service_mock.superuser = True
    new_data = create_document_create_dto("doc1").model_dump(mode="json")
    response = client.post(
        "/api/v1/documents", json=new_data, headers=superuser_header_token
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data == "new.doc.id.0"
    assert document_service_mock.create.call_count == 1
