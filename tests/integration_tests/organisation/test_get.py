import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.integration_tests.setup_db import (
    EXPECTED_CCLW_ORG,
    EXPECTED_UNFCCC_ORG,
    setup_db,
)

EXPECTED_ORG_KEYS = ["internal_name", "description", "display_name", "type", "id"]


@pytest.mark.parametrize(
    "expected_organisation",
    [EXPECTED_CCLW_ORG, EXPECTED_UNFCCC_ORG],
)
def test_get_organisation_by_internal_name(
    client: TestClient, data_db: Session, superuser_header_token, expected_organisation
):
    setup_db(data_db)
    response = client.get(
        f"/api/v1/organisations/{expected_organisation['internal_name']}",
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert set(EXPECTED_ORG_KEYS) == set(data.keys())
    assert data == expected_organisation


@pytest.mark.parametrize(
    "expected_organisation",
    [EXPECTED_CCLW_ORG, EXPECTED_UNFCCC_ORG],
)
def test_get_organisation_by_id(
    client: TestClient, data_db: Session, superuser_header_token, expected_organisation
):
    setup_db(data_db)
    response = client.get(
        f"/api/v1/organisations/{expected_organisation['id']}",
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert set(EXPECTED_ORG_KEYS) == set(data.keys())
    assert data == expected_organisation


def test_get_organisation_non_super(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    response = client.get("/api/v1/organisations/CCLW", headers=user_header_token)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert data["detail"] == "User cclw@cpr.org is not authorised to READ a CORPUS_TYPE"


def test_get_organisation_when_not_authenticated(client: TestClient, data_db: Session):
    setup_db(data_db)
    response = client.get(
        "/api/v1/organisations/CCLW",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_organisation_when_not_found(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/organisations/NonExistentType",
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Organisation not found: NonExistentType"
