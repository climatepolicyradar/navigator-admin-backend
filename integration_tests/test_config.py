from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy.orm import Session
from integration_tests.setup_db import setup_db


def test_get_config(client: TestClient, test_db: Session, user_header_token):
    setup_db(test_db)

    response = client.get(
        "/api/v1/config",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    keys = data.keys()
    assert "geographies" in keys
    assert "taxonomies" in keys
    assert "languages" in keys
