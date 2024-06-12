"""
Tests the routes for collection management.

This uses a service mock and ensures each endpoint calls into the service.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient


def test_delete_when_ok(client: TestClient, collection_service_mock, user_header_token):
    response = client.delete("/api/v1/collections/col1", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    assert collection_service_mock.delete.call_count == 1


@pytest.mark.skip(reason="No admin user for MVP")
def test_delete_collection_fails_if_not_admin(
    client: TestClient, collection_service_mock, user_header_token
):
    response = client.delete("/api/v1/collections/col1", headers=user_header_token)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert collection_service_mock.delete.call_count == 0


def test_delete_when_not_found(
    client: TestClient, collection_service_mock, user_header_token
):
    collection_service_mock.missing = True
    response = client.delete("/api/v1/collections/col1", headers=user_header_token)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Collection not deleted: col1"
    assert collection_service_mock.delete.call_count == 1
