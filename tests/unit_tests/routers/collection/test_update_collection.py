"""
Tests the routes for collection management.

This uses a service mock and ensures each endpoint calls into the service.
"""

from fastapi import status
from fastapi.testclient import TestClient

from tests.helpers.collection import create_collection_write_dto


def test_update_when_ok(client: TestClient, collection_service_mock, user_header_token):
    new_data = create_collection_write_dto().model_dump()
    response = client.put(
        "/api/v1/collections/col1", json=new_data, headers=user_header_token
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "col1"
    assert collection_service_mock.update.call_count == 1


def test_update_when_not_found(
    client: TestClient, collection_service_mock, user_header_token
):
    collection_service_mock.missing = True
    new_data = create_collection_write_dto().model_dump()
    response = client.put(
        "/api/v1/collections/col1", json=new_data, headers=user_header_token
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Collection not updated: col1"
    assert collection_service_mock.update.call_count == 1
