from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.integration_tests.setup_db import (
    EXPECTED_CCLW_ORG,
    EXPECTED_NUM_ORGS,
    EXPECTED_UNFCCC_ORG,
    setup_db,
)

EXPECTED_ORG_KEYS = ["internal_name", "description", "display_name", "type", "id"]


def test_get_all_organisations(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/organisations",
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0  # Ensure there are corpus types returned

    assert len(data) == EXPECTED_NUM_ORGS
    for item in data:
        assert isinstance(item, dict)
        assert all(key in EXPECTED_ORG_KEYS for key in item)

    # Check CCLW content.
    cclw_org = data[2]
    assert cclw_org == EXPECTED_CCLW_ORG

    # Check UNFCCC content.
    unfccc_org = data[1]
    assert unfccc_org == EXPECTED_UNFCCC_ORG


def test_get_all_organisations_non_super(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/organisations",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert (
        data["detail"] == "User cclw@cpr.org is not authorised to READ an ORGANISATION"
    )


def test_get_all_organisations_when_not_authenticated(
    client: TestClient, data_db: Session
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/organisations",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
