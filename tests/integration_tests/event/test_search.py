import logging

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.integration_tests.setup_db import setup_db


def test_search_event(client: TestClient, test_db: Session, user_header_token):
    setup_db(test_db)
    response = client.get(
        "/api/v1/events/?q=Amended",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)

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
    client: TestClient, test_db: Session, user_header_token, caplog
):
    setup_db(test_db)
    with caplog.at_level(logging.INFO):
        response = client.get(
            "/api/v1/events/?q=lemon",
            headers=user_header_token,
        )
    assert response.status_code == status.HTTP_200_OK
    assert (
        "Events not found for terms: {'q': 'lemon', 'max_results': 500}" in caplog.text
    )


def test_search_document_when_db_error(
    client: TestClient, test_db: Session, bad_event_repo, user_header_token
):
    setup_db(test_db)
    response = client.get(
        "/api/v1/events/?q=lemon",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Bad Repo"
    assert bad_event_repo.search.call_count == 1


def test_search_document_with_max_results(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
    response = client.get(
        "/api/v1/events/?q=Amended&max_results=1",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)

    ids_found = set([f["import_id"] for f in data])
    assert len(ids_found) == 1

    expected_ids = set(["E.0.0.2"])
    assert ids_found.symmetric_difference(expected_ids) == set([])


def test_search_document_when_invalid_params(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
    response = client.get(
        "/api/v1/events/?wrong=param",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "Search parameters are invalid: ['wrong']"
