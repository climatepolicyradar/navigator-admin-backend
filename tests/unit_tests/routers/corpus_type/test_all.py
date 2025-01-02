from fastapi import status
from fastapi.testclient import TestClient


def test_all_corpus_type_when_not_authenticated(client: TestClient):
    response = client.get(
        "/api/v1/corpus-types",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_all_corpus_type_when_non_admin_non_super(
    client: TestClient, user_header_token
):
    response = client.get("/api/v1/corpus-types", headers=user_header_token)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_all_corpus_type_when_admin_non_super(
    client: TestClient, admin_user_header_token
):
    response = client.get("/api/v1/corpus-types", headers=admin_user_header_token)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_all_when_ok(
    client: TestClient, superuser_header_token, corpus_type_service_mock
):
    response = client.get("/api/v1/corpus-types", headers=superuser_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["name"] == "test"
    assert corpus_type_service_mock.all.call_count == 1
