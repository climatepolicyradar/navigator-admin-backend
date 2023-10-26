from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy.orm import Session
import app.service.token as token_service
from integration_tests.setup_db import setup_db


def test_login_ok(client: TestClient, test_db: Session):
    setup_db(test_db)

    form_data = {"username": "test@cpr.org", "password": "scruffycode"}

    response = client.post(
        "/api/tokens",
        data=form_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data and "token_type" in data


def families_endpoint_ok(client: TestClient, headers) -> bool:
    response = client.get("/api/v1/analytics/summary", headers=headers)
    return response.status_code == status.HTTP_200_OK
    

def test_encode_for_test():
    t = token_service.encode("cclw@climatepolicyradar.org", False,  {"CCLW":{"is_admin": True}})
    print(t)

def test_token_is_usable(client: TestClient, test_db: Session, user_header_token):
    setup_db(test_db)

    form_data = {"username": "test@cpr.org", "password": "scruffycode"}

    response = client.post(
        "/api/tokens",
        data=form_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data and "token_type" in data

    # Check we can decode it
    result = token_service.decode(data["access_token"])
    assert result.email == "test@cpr.org"

    # Check we can use it in a request
    auth_header = {
        "Authorization": f"Bearer {data['access_token']}"
    }
    # Check the test token
    print(user_header_token)    
    assert families_endpoint_ok(client, user_header_token)

    # Check the token from logging in
    print(auth_header)
    assert families_endpoint_ok(client, auth_header)



def test_login_when_user_inactive(client: TestClient, test_db: Session):
    setup_db(test_db)

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


def test_login_when_user_not_found(client: TestClient, test_db: Session):
    setup_db(test_db)

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


def test_login_when_hashed_password_empty(client: TestClient, test_db: Session):
    setup_db(test_db)

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


def test_login_when_password_mismatch(client: TestClient, test_db: Session):
    setup_db(test_db)

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
