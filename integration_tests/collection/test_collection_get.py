from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy.orm import Session

from integration_tests.setup_db import EXPECTED_COLLECTIONS, setup_db


# --- GET ALL


def test_get_all_collections(client: TestClient, test_db: Session, user_header_token):
    setup_db(test_db)
    response = client.get(
        "/api/v1/collections",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert type(data) is list
    assert len(data) == 2
    ids_found = set([f["import_id"] for f in data])
    expected_ids = set(["C.0.0.1", "C.0.0.2"])

    assert ids_found.symmetric_difference(expected_ids) == set([])

    sdata = sorted(data, key=lambda d: d["import_id"])
    assert sdata[0] == EXPECTED_COLLECTIONS[0]
    assert sdata[1] == EXPECTED_COLLECTIONS[1]


def test_get_all_collections_is_authed(client: TestClient, test_db: Session):
    setup_db(test_db)
    response = client.get(
        "/api/v1/collections",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# --- GET


def test_get_collection(client: TestClient, test_db: Session, user_header_token):
    setup_db(test_db)
    response = client.get(
        "/api/v1/collections/C.0.0.1",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "C.0.0.1"
    assert data == EXPECTED_COLLECTIONS[0]


def test_get_collection_when_not_authenticated(client: TestClient, test_db: Session):
    setup_db(test_db)
    response = client.get(
        "/api/v1/collections/C.0.0.1",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_collection_when_not_found(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
    response = client.get(
        "/api/v1/collections/C.0.0.8",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Collection not found: C.0.0.8"


def test_get_collection_when_id_invalid(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
    response = client.get(
        "/api/v1/collections/A008",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    expected_msg = "The import id A008 is invalid!"
    assert data["detail"] == expected_msg


def test_get_collection_when_db_error(
    client: TestClient, test_db: Session, bad_collection_repo, user_header_token
):
    setup_db(test_db)
    response = client.get(
        "/api/v1/collections/A.0.0.8",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Bad Repo"
