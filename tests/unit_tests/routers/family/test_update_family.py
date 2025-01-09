"""
Tests the routes for family management.

This uses a service mock and ensures each endpoint calls into the service.
"""

from fastapi import status
from fastapi.testclient import TestClient

from tests.helpers.family import create_family_write_dto


def test_update_when_ok(client: TestClient, family_service_mock, user_header_token):
    new_data = create_family_write_dto("fam1").model_dump()
    response = client.put(
        "/api/v1/families/fam1", json=new_data, headers=user_header_token
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "fam1"
    assert family_service_mock.update.call_count == 1


def test_update_when_not_found(
    client: TestClient, family_service_mock, user_header_token
):
    family_service_mock.missing = True
    new_data = create_family_write_dto("fam1").model_dump()
    response = client.put(
        "/api/v1/families/fam1", json=new_data, headers=user_header_token
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Family not updated: fam1"
    assert family_service_mock.update.call_count == 1


def test_update_when_validation_error(
    client: TestClient, family_service_mock, user_header_token
):
    family_service_mock.valid = False
    new_data = create_family_write_dto("fam1").model_dump()
    response = client.put(
        "/api/v1/families/fam1",
        json=new_data,
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "Invalid data"
    assert family_service_mock.update.call_count == 1


def test_update_raises_when_corpus_org_different_to_usr_org(
    client: TestClient, family_service_mock, user_header_token
):
    family_service_mock.org_mismatch = True
    new_data = create_family_write_dto("fam1")
    response = client.put(
        "/api/v1/families/fam1",
        json=new_data.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert data["detail"] == "Org mismatch"
    assert family_service_mock.update.call_count == 1


def test_update_success_when_corpus_org_different_to_usr_org_super(
    client: TestClient, family_service_mock, superuser_header_token
):
    family_service_mock.org_mismatch = True
    family_service_mock.superuser = True
    new_data = create_family_write_dto("fam1").model_dump()
    response = client.put(
        "/api/v1/families/fam1", json=new_data, headers=superuser_header_token
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "fam1"
    assert family_service_mock.update.call_count == 1


def test_update_makes_no_changes_to_geographies_if_property_not_present_in_payload(
    client: TestClient, family_service_mock, user_header_token
):
    new_data = create_family_write_dto("fam1").model_dump()
    response = client.put(
        "/api/v1/families/fam1", json=new_data, headers=user_header_token
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "fam1"
    assert data["geographies"] == []
    assert family_service_mock.update.call_count == 1
