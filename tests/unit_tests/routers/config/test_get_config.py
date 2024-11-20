from fastapi import status
from fastapi.testclient import TestClient


def test_get_when_ok(client: TestClient, user_header_token, config_service_mock):
    response = client.get("/api/v1/config", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    keys = data.keys()
    assert "geographies" in keys
    assert "corpora" in keys
    assert "languages" in keys
    assert "document" in keys
    assert config_service_mock.get.call_count == 1


def test_get_when_db_error(client: TestClient, user_header_token, config_service_mock):
    config_service_mock.throw_repository_error = True
    response = client.get("/api/v1/config", headers=user_header_token)
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
