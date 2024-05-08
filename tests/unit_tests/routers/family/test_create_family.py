"""
Tests the routes for family management.

This uses a service mock and ensures each endpoint calls into the service.
"""

from fastapi import status
from fastapi.testclient import TestClient

from tests.helpers.family import create_family_create_dto


def test_create_when_ok(client: TestClient, family_service_mock, user_header_token):
    new_data = create_family_create_dto("fam1").model_dump()
    response = client.post("/api/v1/families", json=new_data, headers=user_header_token)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data == "new-import-id"
    assert family_service_mock.create.call_count == 1


def test_create_when_org_mismatch(
    client: TestClient, family_service_mock, non_cclw_user_header_token
):
    family_service_mock.org_mismatch = True
    new_data = create_family_create_dto("fam1").model_dump()
    response = client.post(
        "/api/v1/families", json=new_data, headers=non_cclw_user_header_token
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    expected_msg = "Org mismatch"
    assert expected_msg == data["detail"]
    assert family_service_mock.create.call_count == 1


def test_create_when_invalid_data(
    client: TestClient, family_service_mock, user_header_token
):
    family_service_mock.valid = False
    new_data = create_family_create_dto("fam1").model_dump()
    response = client.post("/api/v1/families", json=new_data, headers=user_header_token)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    expected_msg = "Invalid data"
    assert expected_msg == data["detail"]
    assert family_service_mock.create.call_count == 1
