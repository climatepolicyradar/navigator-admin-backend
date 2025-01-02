from fastapi import status
from fastapi.testclient import TestClient


def test_get_corpus_type_when_not_authenticated(client: TestClient):
    response = client.get(
        "/api/v1/corpus-types/test_corpus_type",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_corpus_type_when_non_admin_non_super(
    client: TestClient, user_header_token
):
    response = client.get(
        "/api/v1/corpus-types/test_corpus_type", headers=user_header_token
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_corpus_type_when_admin_non_super(
    client: TestClient, admin_user_header_token
):
    response = client.get(
        "/api/v1/corpus-types/test_corpus_type", headers=admin_user_header_token
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_when_ok(
    client: TestClient, corpus_type_service_mock, superuser_header_token
):
    response = client.get(
        "/api/v1/corpus-types/test_name", headers=superuser_header_token
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "test_name"
    assert corpus_type_service_mock.get.call_count == 1


def test_get_when_not_found(
    client: TestClient, corpus_type_service_mock, superuser_header_token
):
    corpus_type_service_mock.missing = True
    response = client.get(
        "/api/v1/corpus-types/test_corpus_type", headers=superuser_header_token
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Corpus type not found: test_corpus_type"
    assert corpus_type_service_mock.get.call_count == 1
