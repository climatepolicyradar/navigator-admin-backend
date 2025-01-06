from fastapi import status
from fastapi.testclient import TestClient

from tests.helpers.corpus_type import create_corpus_type_create_dto


def test_create_when_ok(
    client: TestClient, corpus_type_service_mock, superuser_header_token
):
    new_data = create_corpus_type_create_dto("test_ct_name").model_dump(mode="json")
    response = client.post(
        "/api/v1/corpus-types", json=new_data, headers=superuser_header_token
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data == "test_ct_name"


def test_create_fails_when_validation_error(
    client: TestClient, corpus_type_service_mock, superuser_header_token
):
    corpus_type_service_mock.throw_validation_error = True
    new_data = create_corpus_type_create_dto("validation_error").model_dump(mode="json")
    response = client.post(
        "/api/v1/corpus-types", json=new_data, headers=superuser_header_token
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "Validation error"
