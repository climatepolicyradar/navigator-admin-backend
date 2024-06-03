import logging

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.integration_tests.setup_db import setup_db


def test_search_document_super(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/documents/?q=title",
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)

    ids_found = set([f["import_id"] for f in data])
    assert len(ids_found) == 3

    expected_ids = set(["D.0.0.1", "D.0.0.2", "D.0.0.3"])
    assert ids_found.symmetric_difference(expected_ids) == set([])


def test_search_document_cclw(client: TestClient, data_db: Session, user_header_token):
    setup_db(data_db)
    response = client.get(
        "/api/v1/documents/?q=title",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)

    ids_found = set([f["import_id"] for f in data])
    assert len(ids_found) == 1

    expected_ids = set(["D.0.0.3"])
    assert ids_found.symmetric_difference(expected_ids) == set([])


def test_search_document_unfccc(
    client: TestClient, data_db: Session, non_cclw_user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/documents/?q=title",
        headers=non_cclw_user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)

    ids_found = set([f["import_id"] for f in data])
    assert len(ids_found) == 2

    expected_ids = set(["D.0.0.1", "D.0.0.2"])
    assert ids_found.symmetric_difference(expected_ids) == set([])


def test_search_document_when_not_authorised(client: TestClient, data_db: Session):
    setup_db(data_db)
    response = client.get(
        "/api/v1/documents/?q=orange",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_search_document_when_nothing_found(
    client: TestClient, data_db: Session, user_header_token, caplog
):
    setup_db(data_db)
    with caplog.at_level(logging.INFO):
        response = client.get(
            "/api/v1/documents/?q=chicken",
            headers=user_header_token,
        )
    assert response.status_code == status.HTTP_200_OK
    assert (
        "Documents not found for terms: {'q': 'chicken', 'max_results': 500}"
        in caplog.text
    )


def test_search_document_when_db_error(
    client: TestClient, data_db: Session, bad_document_repo, user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/documents/?q=chicken",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Bad Repo"
    assert bad_document_repo.search.call_count == 1


def test_search_document_with_max_results(
    client: TestClient, data_db: Session, non_cclw_user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/documents/?q=title&max_results=1",
        headers=non_cclw_user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)

    ids_found = set([f["import_id"] for f in data])
    assert len(ids_found) == 1

    expected_ids = set(["D.0.0.1"])
    assert ids_found.symmetric_difference(expected_ids) == set([])


def test_search_document_when_invalid_params(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/documents/?wrong=param",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "Search parameters are invalid: ['wrong']"
