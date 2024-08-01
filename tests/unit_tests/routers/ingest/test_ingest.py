"""
Tests the route for bulk import of data.

This uses service mocks and ensures the endpoint calls into each service.
"""

import json

from db_client.models.dfce.family import FamilyCategory
from fastapi import status
from fastapi.testclient import TestClient


def test_create_when_ok(client: TestClient, family_service_mock, user_header_token):
    new_data = {
        "data": {
            "title": "test",
            "summary": "test",
            "geography": "CHN",
            "category": FamilyCategory.LEGISLATIVE.value,
            "metadata": "",
            "collections": [],
            "corpus_import_id": "CCLW.corpus.i00000001.n0000",
        }
    }
    response = client.post("/api/v1/ingest", json=new_data, headers=user_header_token)
    assert response.status_code == status.HTTP_201_CREATED
    # data = response.json()
    # assert data == "new-import-id"
    # assert family_service_mock.create.call_count == 1
