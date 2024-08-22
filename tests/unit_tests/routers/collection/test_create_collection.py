"""
Tests the routes for collection management.

This uses a service mock and ensures each endpoint calls into the service.
"""

from fastapi import status
from fastapi.testclient import TestClient

from tests.helpers.collection import create_collection_create_dto


def test_create_when_ok(client: TestClient, collection_service_mock, user_header_token):
    new_data = create_collection_create_dto().model_dump()
    response = client.post(
        "/api/v1/collections", json=new_data, headers=user_header_token
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data == "test.new.collection.0"
    assert collection_service_mock.create.call_count == 1
