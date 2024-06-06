"""
Tests the routes for family management.

This uses a service mock and ensures each endpoint calls into the service.
"""

from fastapi import status
from fastapi.testclient import TestClient


def test_delete_when_ok(client: TestClient, family_service_mock, user_header_token):
    response = client.delete("/api/v1/families/fam1", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    assert family_service_mock.delete.call_count == 1


def test_delete_when_not_found(
    client: TestClient, family_service_mock, user_header_token
):
    family_service_mock.missing = True
    response = client.delete("/api/v1/families/fam1", headers=user_header_token)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Family not deleted: fam1"
    assert family_service_mock.delete.call_count == 1


def test_delete_fails_when_invalid_org(
    client: TestClient, family_service_mock, user_header_token
):
    family_service_mock.throw_validation_error = True
    response = client.delete("/api/v1/families/fam1", headers=user_header_token)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert family_service_mock.delete.call_count == 1


def test_delete_fails_when_org_mismatch(
    client: TestClient, family_service_mock, user_header_token
):
    family_service_mock.org_mismatch = True
    response = client.delete("/api/v1/families/fam1", headers=user_header_token)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert family_service_mock.delete.call_count == 1


def test_delete_success_when_org_mismatch(
    client: TestClient, family_service_mock, superuser_header_token
):
    family_service_mock.org_mismatch = True
    family_service_mock.superuser = True
    response = client.delete("/api/v1/families/fam1", headers=superuser_header_token)
    assert response.status_code == status.HTTP_200_OK
    assert family_service_mock.delete.call_count == 1
