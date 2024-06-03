from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.integration_tests.setup_db import EXPECTED_COLLECTIONS, setup_db


def test_get_collection(client: TestClient, data_db: Session, user_header_token):
    setup_db(data_db)
    response = client.get(
        "/api/v1/collections/C.0.0.1",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "C.0.0.1"

    assert all(field in data for field in ("created", "last_modified"))
    expected_data = {
        k: v for k, v in data.items() if k not in ("created", "last_modified")
    }
    assert expected_data == EXPECTED_COLLECTIONS[0]


def test_get_collection_when_not_authenticated(client: TestClient, data_db: Session):
    setup_db(data_db)
    response = client.get(
        "/api/v1/collections/C.0.0.1",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_collection_when_not_found(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/collections/C.0.0.8",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Collection not found: C.0.0.8"


def test_get_collection_when_id_invalid(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/collections/A008",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    expected_msg = "The import id A008 is invalid!"
    assert data["detail"] == expected_msg


def test_get_collection_when_db_error(
    client: TestClient, data_db: Session, bad_collection_repo, user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/collections/A.0.0.8",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Bad Repo"
