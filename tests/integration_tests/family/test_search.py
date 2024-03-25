import logging

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.integration_tests.setup_db import setup_db


def test_search_family_using_q(client: TestClient, test_db: Session, user_header_token):
    setup_db(test_db)
    response = client.get(
        "/api/v1/families/?q=orange",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)

    ids_found = set([f["import_id"] for f in data])
    assert len(ids_found) == 2

    expected_ids = set(["A.0.0.2", "A.0.0.3"])
    assert ids_found.symmetric_difference(expected_ids) == set([])


def test_search_family_with_specific_param(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
    response = client.get(
        "/api/v1/families/?summary=apple",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)

    ids_found = set([f["import_id"] for f in data])
    assert len(ids_found) == 1

    expected_ids = set(["A.0.0.2"])
    assert ids_found.symmetric_difference(expected_ids) == set([])


def test_search_family_with_max_results(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
    response = client.get(
        "/api/v1/families/?q=orange&max_results=1",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)

    ids_found = set([f["import_id"] for f in data])
    assert len(ids_found) == 1

    expected_ids = set(["A.0.0.2"])
    assert ids_found.symmetric_difference(expected_ids) == set([])


def test_search_family_when_not_authenticated(client: TestClient, test_db: Session):
    setup_db(test_db)
    response = client.get(
        "/api/v1/families/?q=orange",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_search_family_when_not_found(
    client: TestClient, test_db: Session, user_header_token, caplog
):
    setup_db(test_db)
    with caplog.at_level(logging.INFO):
        response = client.get(
            "/api/v1/families/?q=chicken",
            headers=user_header_token,
        )
    assert response.status_code == status.HTTP_200_OK
    assert (
        "Families not found for terms: {'q': 'chicken', 'max_results': 500}"
        in caplog.text
    )


def test_search_family_when_invalid_params(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
    response = client.get(
        "/api/v1/families/?wrong=param",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "Search parameters are invalid: ['wrong']"


def test_search_family_when_db_error(
    client: TestClient, test_db: Session, bad_family_repo, user_header_token
):
    setup_db(test_db)
    response = client.get(
        "/api/v1/families/?q=error",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Bad Repo"
    assert bad_family_repo.search.call_count == 1
