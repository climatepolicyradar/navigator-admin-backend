from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.integration_tests.setup_db import setup_db


def test_get_all_users(client: TestClient, data_db: Session, superuser_header_token):
    setup_db(data_db)
    response = client.get("/api/v1/users", headers=superuser_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    for user in data:
        assert "email" in user
        assert "name" in user
        assert "is_superuser" in user
        assert "organisations" in user


def test_get_all_users_non_superuser(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    response = client.get("/api/v1/users", headers=user_header_token)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_all_users_unauthenticated(client: TestClient, data_db: Session):
    setup_db(data_db)
    response = client.get("/api/v1/users")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_user_by_email(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    response = client.get("/api/v1/users/cclw@cpr.org", headers=superuser_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "cclw@cpr.org"
    assert data["name"] == "CCLWTestUser"
    assert data["is_superuser"] is False
    assert isinstance(data["organisations"], list)
    assert len(data["organisations"]) == 1


def test_get_user_not_found(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/users/nobody@cpr.org", headers=superuser_header_token
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
