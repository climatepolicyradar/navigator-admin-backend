"""
Tests the route for bulk import of data.

This uses service mocks and ensures the endpoint calls into each service.
"""

import io
import json

from fastapi import status
from fastapi.testclient import TestClient


def test_ingest_when_not_authenticated(client: TestClient):
    response = client.post(
        "/api/v1/ingest/test",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_ingest_when_ok(
    client: TestClient,
    user_header_token,
    collection_repo_mock,
    corpus_repo_mock,
    family_repo_mock,
    geography_repo_mock,
    db_client_metadata_mock,
):

    response = client.post(
        "/api/v1/ingest/test",
        files={"new_data": open("tests/unit_tests/routers/ingest/test.json", "rb")},
        headers=user_header_token,
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {
        "collections": ["test.new.collection.0", "test.new.collection.0"],
        "families": ["created", "created"],
        # "families": ["test.new.family.0", "test.new.family.0"],
    }


def test_ingest_collections_when_import_id_wrong_format(
    client: TestClient, user_header_token, corpus_service_mock
):

    invalid_import_id = "invalid"
    test_data = json.dumps(
        {
            "collections": [
                {
                    "import_id": invalid_import_id,
                    "title": "Test title",
                    "description": "Test description",
                },
            ],
            "families": [],
        }
    ).encode("utf-8")
    test_data_file = io.BytesIO(test_data)

    response = client.post(
        "/api/v1/ingest/test",
        files={"new_data": test_data_file},
        headers=user_header_token,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json().get("detail") == "The import id invalid is invalid!"


def test_ingest_collections_when_no_collections(
    client: TestClient, user_header_token, collection_repo_mock, corpus_service_mock
):
    test_data = json.dumps({"collections": [], "families": []}).encode("utf-8")
    test_data_file = io.BytesIO(test_data)
    response = client.post(
        "/api/v1/ingest/test",
        files={"new_data": test_data_file},
        headers=user_header_token,
    )

    assert collection_repo_mock.create.call_count == 0

    assert response.status_code == status.HTTP_204_NO_CONTENT
