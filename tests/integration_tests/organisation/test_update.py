from db_client.models.organisation import Organisation
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.model.organisation import OrganisationReadDTO, OrganisationWriteDTO


def test_successfully_updates_an_existing_organisation(
    client: TestClient, data_db: Session, superuser_header_token
):
    id = 100
    existing_organisation = Organisation(
        id=id,
        name="Test Organisation",
        display_name="Test Organisation",
        description="Test Description",
        organisation_type="ORG",
        attribution_url="test_org_attribution_url.com",
    )
    data_db.add(existing_organisation)
    data_db.commit()

    updated_organisation = OrganisationWriteDTO(
        internal_name="Test Organisation - Edited",
        display_name="Test Organisation - Edited",
        description="Test Description - Edited",
        type="ORG - Edited",
        attribution_url="test_org_attribution_url_edited.com",
    )

    expected_update_response = OrganisationReadDTO(
        id=id,
        internal_name=updated_organisation.internal_name,
        display_name=updated_organisation.display_name,
        description=updated_organisation.description,
        type=updated_organisation.type,
        attribution_url=updated_organisation.attribution_url,
    ).model_dump()

    response = client.put(
        f"/api/v1/organisations/{id}",
        headers=superuser_header_token,
        json=updated_organisation.model_dump(),
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data == expected_update_response

    saved_organisation = data_db.query(Organisation).filter(Organisation.id == id).one()

    assert saved_organisation.name == updated_organisation.internal_name
    assert saved_organisation.display_name == updated_organisation.display_name
    assert saved_organisation.description == updated_organisation.description
    assert saved_organisation.organisation_type == updated_organisation.type
    assert saved_organisation.attribution_url == updated_organisation.attribution_url


def test_successfully_updates_an_existing_organisation_with_attribution_url(
    client: TestClient, data_db: Session, superuser_header_token
):
    id = 100
    existing_organisation = Organisation(
        id=id,
        name="Test Organisation",
        display_name="Test Organisation",
        description="Test Description",
        organisation_type="ORG",
        attribution_url="test_org_attribution_url.com",
    )
    data_db.add(existing_organisation)
    data_db.commit()

    updated_organisation = OrganisationWriteDTO(
        internal_name="Test Organisation - Edited",
        display_name="Test Organisation - Edited",
        description="Test Description - Edited",
        type="ORG - Edited",
        attribution_url=None,
    )

    expected_update_response = OrganisationReadDTO(
        id=id,
        internal_name=updated_organisation.internal_name,
        display_name=updated_organisation.display_name,
        description=updated_organisation.description,
        type=updated_organisation.type,
        attribution_url=updated_organisation.attribution_url,
    ).model_dump()

    response = client.put(
        f"/api/v1/organisations/{id}",
        headers=superuser_header_token,
        json=updated_organisation.model_dump(),
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data == expected_update_response

    saved_organisation = data_db.query(Organisation).filter(Organisation.id == id).one()

    assert saved_organisation.name == updated_organisation.internal_name
    assert saved_organisation.attribution_url == updated_organisation.attribution_url


def test_update_idempotency(
    client: TestClient, data_db: Session, superuser_header_token
):
    id = 100

    update_organisation = {
        "internal_name": "Test Organisation",
        "display_name": "Test Organisation",
        "description": "Test Description",
        "type": "ORG",
        "attribution_url": "test_org_attribution_url.com",
    }

    existing_organisation = Organisation(
        id=id,
        name="Test Organisation",
        display_name="Test Organisation",
        description="Test Description",
        organisation_type="ORG",
        attribution_url="test_org_attribution_url.com",
    )
    data_db.add(existing_organisation)
    data_db.flush()

    response = client.put(
        f"/api/v1/organisations/{id}",
        headers=superuser_header_token,
        json=update_organisation,
    )

    assert response.status_code == status.HTTP_200_OK

    saved_organisation = data_db.query(Organisation).filter(Organisation.id == id).one()

    assert saved_organisation.name == update_organisation["internal_name"]
    assert saved_organisation.display_name == update_organisation["display_name"]
    assert saved_organisation.description == update_organisation["description"]
    assert saved_organisation.organisation_type == update_organisation["type"]
    assert saved_organisation.attribution_url == update_organisation["attribution_url"]


def test_returns_404_status_code_if_organisation_not_found(
    client: TestClient, data_db: Session, superuser_header_token
):
    id = 100
    updated_organisation = OrganisationWriteDTO(
        internal_name="Test Organisation - Edited",
        display_name="Test Organisation - Edited",
        description="Test Description - Edited",
        type="ORG - Edited",
        attribution_url="test_org_attribution_url_edited.com",
    )

    response = client.put(
        f"/api/v1/organisations/{id}",
        headers=superuser_header_token,
        json=updated_organisation.model_dump(),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == f"Unable to find organisation to update for id: {id}"


def test_update_organisation_when_not_authorised(client: TestClient, data_db: Session):
    id = 100
    updated_organisation = OrganisationWriteDTO(
        internal_name="Test Organisation - Edited",
        display_name="Test Organisation - Edited",
        description="Test Description - Edited",
        type="ORG - Edited",
        attribution_url="test_org_attribution_url_edited.com",
    )

    response = client.put(
        f"/api/v1/organisations/{id}",
        json=updated_organisation.model_dump(),
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_does_not_update_organisation_on_error(
    client: TestClient,
    data_db: Session,
    superuser_header_token,
    rollback_organisation_repo,
):
    id = 100
    original_organisation = Organisation(
        id=id,
        name="Test Organisation",
        display_name="Test Organisation",
        description="Test Description",
        organisation_type="ORG",
        attribution_url="test_org_attribution_url.com",
    )
    data_db.add(original_organisation)
    data_db.commit()

    updated_organisation = OrganisationWriteDTO(
        internal_name="Test Organisation - Edited",
        display_name="Test Organisation - Edited",
        description="Test Description - Edited",
        type="ORG - Edited",
        attribution_url="test_org_attribution_url_edited.com",
    )

    response = client.put(
        f"/api/v1/organisations/{id}",
        headers=superuser_header_token,
        json=updated_organisation.model_dump(),
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    data = response.json()
    assert data["detail"] == f"Error updating organisation: {id}"

    assert (
        data_db.query(Organisation).filter(Organisation.id == id).one_or_none()
        == original_organisation
    )
