from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from integration_tests.setup_db import setup_db


def test_login_ok(client: TestClient, data_db: Session):
    setup_db(data_db)

    form_data = {"username": "test@cpr.org", "password": "scruffycode"}

    response = client.post(
        "/api/tokens",
        data=form_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data and "token_type" in data


def test_login_when_user_inactive(client: TestClient, data_db: Session):
    setup_db(data_db)

    email = "test1@cpr.org"
    form_data = {"username": email, "password": "apple"}

    response = client.post(
        "/api/tokens",
        data=form_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["detail"] == "Incorrect username or password"


def test_login_when_user_not_found(client: TestClient, data_db: Session):
    setup_db(data_db)

    email = "test@test.org"
    form_data = {"username": email, "password": "banana"}

    response = client.post(
        "/api/tokens",
        data=form_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["detail"] == "Incorrect username or password"


def test_login_when_hashed_password_empty(client: TestClient, data_db: Session):
    setup_db(data_db)

    email = "test2@cpr.org"
    form_data = {"username": email, "password": "cherry"}

    response = client.post(
        "/api/tokens",
        data=form_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["detail"] == "Incorrect username or password"


def test_login_when_password_mismatch(client: TestClient, data_db: Session):
    setup_db(data_db)

    email = "test3@cpr.org"
    form_data = {"username": email, "password": "date"}

    response = client.post(
        "/api/tokens",
        data=form_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["detail"] == "Incorrect username or password"
