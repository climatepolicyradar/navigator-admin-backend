from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy.orm import Session

from integration_tests.setup_db import (
    EXPECTED_ANALYTICS_SUMMARY,
    EXPECTED_ANALYTICS_SUMMARY_KEYS,
    setup_db,
)


# --- GET ALL


def test_get_all_analytics(client: TestClient, test_db: Session, user_header_token):
    setup_db(test_db)
    response = client.get(
        "/api/v1/analytics",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_all_analytics_when_not_authenticated(client: TestClient, test_db: Session):
    setup_db(test_db)
    response = client.get(
        "/api/v1/analytics",
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


# --- GET SUMMARY


def test_get_analytics_summary(client: TestClient, test_db: Session, user_header_token):
    setup_db(test_db)
    response = client.get(
        "/api/v1/analytics/summary",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert isinstance(data, dict)
    assert list(data.keys()) == EXPECTED_ANALYTICS_SUMMARY_KEYS

    assert dict(sorted(data.items())) == dict(
        sorted(EXPECTED_ANALYTICS_SUMMARY.items())
    )


def test_get_analytics_summary_when_not_authenticated(
    client: TestClient, test_db: Session
):
    setup_db(test_db)
    response = client.get(
        "/api/v1/analytics/summary",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_analytics_summary_when_not_found(
    client: TestClient, test_db: Session, collection_count_none, user_header_token
):
    setup_db(test_db, configure_empty=True)
    response = client.get(
        "/api/v1/analytics/summary",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Analytics summary not found"


def test_get_analytics_when_collection_db_error(
    client: TestClient, test_db: Session, bad_collection_repo, user_header_token
):
    setup_db(test_db)
    response = client.get(
        "/api/v1/analytics/summary",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Bad Repo"


def test_get_analytics_when_family_db_error(
    client: TestClient, test_db: Session, bad_family_repo, user_header_token
):
    setup_db(test_db)
    response = client.get(
        "/api/v1/analytics/summary",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Bad Repo"


def test_get_analytics_when_document_db_error(
    client: TestClient, test_db: Session, bad_document_repo, user_header_token
):
    setup_db(test_db)
    response = client.get(
        "/api/v1/analytics/summary",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Bad Repo"
