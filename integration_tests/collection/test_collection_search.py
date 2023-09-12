from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy.orm import Session
from integration_tests.setup_db import setup_db


def test_search_collection(client: TestClient, test_db: Session, user_header_token):
    setup_db(test_db)
    response = client.get(
        "/api/v1/collections/?q=big",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert type(data) is list

    ids_found = set([f["import_id"] for f in data])
    assert len(ids_found) == 1

    expected_ids = set(["C.0.0.1"])
    assert ids_found.symmetric_difference(expected_ids) == set([])


def test_search_collection_is_authed(client: TestClient, test_db: Session):
    setup_db(test_db)
    response = client.get(
        "/api/v1/collections/?q=orange",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_search_collection_404(client: TestClient, test_db: Session, user_header_token):
    setup_db(test_db)
    response = client.get(
        "/api/v1/collections/?q=chicken",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Collections not found for term: chicken"
