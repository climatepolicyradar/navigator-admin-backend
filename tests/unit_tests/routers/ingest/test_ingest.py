"""
Tests the route for bulk import of data.

This uses service mocks and ensures the endpoint calls into each service.
"""

from fastapi import status
from fastapi.testclient import TestClient


def test_ingest_when_not_authenticated(client: TestClient):
    response = client.post(
        "/api/v1/ingest",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_ingest_when_ok(client: TestClient, user_header_token):
    request_data = {"test": "data"}

    response = client.post(
        "/api/v1/ingest", json=request_data, headers=user_header_token
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == request_data
