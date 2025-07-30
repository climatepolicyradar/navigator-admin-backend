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
