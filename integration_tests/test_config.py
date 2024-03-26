from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from integration_tests.setup_db import setup_db


def test_get_config(client: TestClient, data_db: Session, user_header_token):
    setup_db(data_db)

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
    assert "document" in keys
    assert "event" in keys

    # Now sanity check the data
    assert data["geographies"][1]["node"]["slug"] == "south-asia"

    assert "CCLW" in data["taxonomies"].keys()

    assert "aaa" in data["languages"].keys()

    assert "AMENDMENT" in data["document"]["roles"]
    assert "Action Plan" in data["document"]["types"]
    assert "Translation" in data["document"]["variants"]

    assert "Appealed" in data["event"]["types"]
