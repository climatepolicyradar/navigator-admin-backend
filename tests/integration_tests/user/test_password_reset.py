from fastapi import status
from fastapi.testclient import TestClient


def test_password_reset_returns_status_200_and_new_password_on_success(
    client: TestClient, superuser_header_token
):
    response = client.post(
        "/api/v1/users/cclw@cpr.org/password-reset",
        headers=superuser_header_token,
    )

    assert response.status_code == status.HTTP_200_OK

    new_password = response.json()
    assert new_password


def test_password_reset_does_not_cache_new_password(
    client: TestClient, superuser_header_token
):
    response = client.post(
        "/api/v1/users/cclw@cpr.org/password-reset",
        headers=superuser_header_token,
    )

    assert response.headers["Cache-Control"] == "no-store"
