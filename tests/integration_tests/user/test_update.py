from db_client.models.organisation import Organisation, OrganisationUser
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.integration_tests.setup_db import setup_db


def test_update_user_adds_org_membership(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    unfccc = data_db.query(Organisation).filter(Organisation.name == "UNFCCC").one()

    response = client.put(
        "/api/v1/users/cclw@cpr.org",
        headers=superuser_header_token,
        json={"organisations": [{"id": unfccc.id, "is_admin": False}]},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "cclw@cpr.org"
    org_ids = [o["id"] for o in data["organisations"]]
    assert unfccc.id in org_ids


def test_update_user_replaces_org_memberships(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    cclw = data_db.query(Organisation).filter(Organisation.name == "CCLW").one()
    unfccc = data_db.query(Organisation).filter(Organisation.name == "UNFCCC").one()

    response = client.put(
        "/api/v1/users/cclw@cpr.org",
        headers=superuser_header_token,
        json={
            "organisations": [
                {"id": cclw.id, "is_admin": False},
                {"id": unfccc.id, "is_admin": True},
            ]
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    org_ids = [o["id"] for o in data["organisations"]]
    assert cclw.id in org_ids
    assert unfccc.id in org_ids

    rows = (
        data_db.query(OrganisationUser)
        .filter(OrganisationUser.appuser_email == "cclw@cpr.org")
        .all()
    )
    assert len(rows) == 2


def test_update_user_updates_name(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    cclw = data_db.query(Organisation).filter(Organisation.name == "CCLW").one()

    response = client.put(
        "/api/v1/users/cclw@cpr.org",
        headers=superuser_header_token,
        json={
            "name": "New Name",
            "organisations": [{"id": cclw.id, "is_admin": False}],
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "New Name"


def test_update_user_invalid_org(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    response = client.put(
        "/api/v1/users/cclw@cpr.org",
        headers=superuser_header_token,
        json={"organisations": [{"id": 99999, "is_admin": False}]},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_update_user_not_found(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    cclw = data_db.query(Organisation).filter(Organisation.name == "CCLW").one()
    response = client.put(
        "/api/v1/users/nobody@cpr.org",
        headers=superuser_header_token,
        json={"organisations": [{"id": cclw.id, "is_admin": False}]},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_user_non_superuser(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    response = client.put(
        "/api/v1/users/cclw@cpr.org",
        headers=user_header_token,
        json={"organisations": []},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
