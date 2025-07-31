from db_client.models.organisation import Organisation
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.model.organisation import OrganisationCreateDTO


def test_successfully_creates_an_organisation(
    client: TestClient, data_db: Session, superuser_header_token
):
    new_organisation = OrganisationCreateDTO(
        internal_name="Test Organisation",
        display_name="Test Organisation",
        description="Test Description",
        type="ORG",
        attribution_url="test_org_attribution_url.com",
    )

    response = client.post(
        "/api/v1/organisations",
        headers=superuser_header_token,
        json=new_organisation.model_dump(),
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    # check that the response contains an id of the created organisation
    assert type(data) is int

    created_organisation = (
        data_db.query(Organisation).filter(Organisation.id == data).one()
    )

    assert created_organisation.name == new_organisation.internal_name
    assert created_organisation.display_name == new_organisation.display_name
    assert created_organisation.description == new_organisation.description
    assert created_organisation.organisation_type == new_organisation.type
    assert created_organisation.attribution_url == new_organisation.attribution_url


def test_does_not_create_a_new_organisation_on_error(
    client: TestClient,
    data_db: Session,
    superuser_header_token,
    rollback_organisation_repo,
):
    new_organisation = OrganisationCreateDTO(
        internal_name="Test Organisation",
        display_name="Test Organisation",
        description="Test Description",
        type="ORG",
        attribution_url="test_org_attribution_url.com",
    )

    response = client.post(
        "/api/v1/organisations",
        headers=superuser_header_token,
        json=new_organisation.model_dump(),
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    data = response.json()
    assert data["detail"] == "Error creating an organisation"

    saved_organisations = [org.name for org in data_db.query(Organisation).all()]

    assert new_organisation.internal_name not in saved_organisations


def test_create_when_unauthorised(
    client: TestClient,
    data_db: Session,
):
    new_organisation = OrganisationCreateDTO(
        internal_name="Test Organisation",
        display_name="Test Organisation",
        description="Test Description",
        type="ORG",
        attribution_url="test_org_attribution_url.com",
    )

    response = client.post(
        "/api/v1/organisations",
        json=new_organisation.model_dump(),
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
