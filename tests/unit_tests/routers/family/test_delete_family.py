"""
Tests the routes for family management.

This uses a service mock and ensures each endpoint calls into the service.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient


def test_delete_when_ok(
    client: TestClient, family_service_mock, admin_user_header_token
):
    response = client.delete("/api/v1/families/fam1", headers=admin_user_header_token)
    assert response.status_code == status.HTTP_200_OK
    assert family_service_mock.delete.call_count == 1


@pytest.mark.skip(reason="No admin user for MVP")
def test_delete_fails_when_not_admin(
    client: TestClient, family_service_mock, user_header_token
):
    response = client.delete("/api/v1/families/fam1", headers=user_header_token)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert family_service_mock.delete.call_count == 0


def test_delete_when_not_found(
    client: TestClient, family_service_mock, admin_user_header_token
):
    family_service_mock.missing = True
    response = client.delete("/api/v1/families/fam1", headers=admin_user_header_token)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Family not deleted: fam1"
    assert family_service_mock.delete.call_count == 1


def test_delete_fails_when_org_mismatch(
    client: TestClient, family_service_mock, user_header_token
):
    family_service_mock.throw_validation_error = True
    response = client.delete("/api/v1/families/fam1", headers=user_header_token)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert family_service_mock.delete.call_count == 1
