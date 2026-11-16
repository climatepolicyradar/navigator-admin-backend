from unittest.mock import patch

from db_client.models.organisation import AppUser
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.errors import RepositoryError
from app.service.authentication import get_password_hash
from tests.integration_tests.setup_db import setup_db


def test_password_reset_returns_status_200_and_new_password_for_existing_user(
    client: TestClient, data_db: Session, superuser_header_token
):
    old_password = "test-password"
    old_hashed_password = get_password_hash(old_password)
    existing_user = AppUser(
        email="cclw@cpr.org",
        name="Test User",
        hashed_password=old_hashed_password,
        is_superuser=False,
    )
    data_db.add(existing_user)
    data_db.commit()

    response = client.post(
        "/api/v1/users/cclw@cpr.org/password-reset",
        headers=superuser_header_token,
    )

    assert response.status_code == status.HTTP_200_OK
    new_password = response.json().get("password")
    assert new_password != old_password


def test_password_reset_does_not_allow_response_to_be_cached(
    client: TestClient, data_db: Session, superuser_header_token
):
    existing_user = AppUser(
        email="cclw@cpr.org",
        name="Test User",
        hashed_password="test-password",
        is_superuser=False,
    )
    data_db.add(existing_user)
    data_db.commit()

    response = client.post(
        "/api/v1/users/cclw@cpr.org/password-reset",
        headers=superuser_header_token,
    )

    assert response.headers["Cache-Control"] == "no-store"


def test_password_reset_returns_status_404_NOT_FOUND_when_user_not_found(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)

    invalid_email = "non-existent-user@cpr.org"
    response = client.post(
        f"/api/v1/users/{invalid_email}/password-reset",
        headers=superuser_header_token,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == f"User not found: {invalid_email}"


def test_password_reset_returns_status_503_SERVICE_UNAVAILABLE_on_db_error(
    client: TestClient, superuser_header_token
):
    repository_error = RepositoryError()

    with patch("app.service.app_user.reset_password", side_effect=repository_error):
        response = client.post(
            "/api/v1/users/cclw@cpr.org/password-reset",
            headers=superuser_header_token,
        )

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
