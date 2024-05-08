from fastapi import status
from fastapi.testclient import TestClient

from tests.mocks.repos.app_user_repo import PLAIN_PASSWORD, VALID_USERNAME


def test_get_token(client: TestClient, app_user_repo_mock):
    login_data = {
        "username": VALID_USERNAME,
        "password": PLAIN_PASSWORD,
    }

    response = client.post("/api/tokens", data=login_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data.keys()
    assert len(data["access_token"]) > 200
    assert "token_type" in data.keys()
    assert data["token_type"] == "bearer"


def test_get_token_missing_user(client: TestClient, app_user_repo_mock):
    app_user_repo_mock.error = True

    login_data = {
        "username": VALID_USERNAME,
        "password": PLAIN_PASSWORD,
    }

    response = client.post("/api/tokens", data=login_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert "detail" in data.keys()
    assert data["detail"] == "Incorrect username or password"


def test_get_token_wrong_password(client: TestClient, app_user_repo_mock):
    login_data = {
        "username": VALID_USERNAME,
        "password": "password",
    }

    response = client.post("/api/tokens", data=login_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert "detail" in data.keys()
    assert data["detail"] == "Incorrect username or password"
