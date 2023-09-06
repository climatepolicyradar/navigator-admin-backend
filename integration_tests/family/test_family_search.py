from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy.orm import Session
from integration_tests.family.family_helpers import setup_db


def test_search_family(client: TestClient, test_db: Session, user_header_token):
    setup_db(test_db)
    response = client.get(
        "/api/v1/families/?q=orange",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert type(data) is list

    ids_found = set([f["import_id"] for f in data])
    assert len(ids_found) == 2

    expected_ids = set(["A.0.0.2", "A.0.0.3"])
    assert ids_found.symmetric_difference(expected_ids) == set([])


def test_search_family_is_authed(client: TestClient, test_db: Session):
    setup_db(test_db)
    response = client.get(
        "/api/v1/families/?q=orange",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_search_family_404(client: TestClient, test_db: Session, user_header_token):
    setup_db(test_db)
    response = client.get(
        "/api/v1/families/?q=chicken",
        headers=user_header_token,
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Families not found for term: chicken"
