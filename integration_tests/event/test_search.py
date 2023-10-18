from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy.orm import Session
from integration_tests.setup_db import setup_db


def test_search_event(client: TestClient, test_db: Session, user_header_token):
    setup_db(test_db)
    response = client.get(
        "/api/v1/events/?q=Amended",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert type(data) is list

    ids_found = set([f["import_id"] for f in data])
    assert len(ids_found) == 2

    expected_ids = set(["E.0.0.2", "E.0.0.3"])
    assert ids_found.symmetric_difference(expected_ids) == set([])


def test_search_event_when_not_authorised(client: TestClient, test_db: Session):
    setup_db(test_db)
    response = client.get(
        "/api/v1/events/?q=cabbages",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_search_event_when_nothing_found(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
    response = client.get(
        "/api/v1/events/?q=lemon",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Events not found for term: lemon"


def test_search_event_when_db_error(
    client: TestClient, test_db: Session, bad_event_repo, user_header_token
):
    setup_db(test_db)
    response = client.get(
        "/api/v1/events/?q=lemon",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert bad_event_repo.search.call_count == 1
