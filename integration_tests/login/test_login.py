from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy.orm import Session

from integration_tests.setup_db import setup_db


def test_get_login(client: TestClient, test_db: Session):
    setup_db(test_db)

    form_data = {"username": "test@cpr.org", "password": "scruffycode"}

    response = client.post(
        "/api/tokens",
        data=form_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    print(data)
