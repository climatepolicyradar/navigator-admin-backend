"""
Tests the route for bulk import of data.

This uses service mocks and ensures the endpoint calls into each service.
"""

from fastapi import status
from fastapi.testclient import TestClient

from tests.helpers.family import create_family_create_dto


def test_ingest_when_not_authenticated(client: TestClient):
    response = client.post(
        "/api/v1/ingest",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_ingest_when_ok(client: TestClient, user_header_token):
    new_family_data = create_family_create_dto("fam1").model_dump(mode="json")
    new_family = {
        "name": new_family_data["title"],
        "summary": new_family_data["summary"],
        "metadata": [],
        "events": [],
        "documents": [],
    }

    new_data = {"corpus_id": "test", "families": [new_family]}

    response = client.post("/api/v1/ingest", json=new_data, headers=user_header_token)
    assert response.status_code == status.HTTP_201_CREATED
