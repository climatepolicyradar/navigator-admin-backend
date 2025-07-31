from fastapi import status
from fastapi.testclient import TestClient

from app.model.organisation import OrganisationCreateDTO


def test_create_returns_503_on_repository_error(
    client: TestClient, superuser_header_token, organisation_repo_mock
):
    organisation_repo_mock.throw_repository_error = True

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

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Repository Error: Bad organisation repo"
