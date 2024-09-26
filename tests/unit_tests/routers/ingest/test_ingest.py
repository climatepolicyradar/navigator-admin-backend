"""
Tests the route for bulk import of data.

This uses service mocks and ensures the endpoint calls into each service.
"""

import io
import json
import os
from unittest.mock import Mock, patch

from fastapi import status
from fastapi.testclient import TestClient


def test_ingest_when_not_authenticated(client: TestClient):
    response = client.post(
        "/api/v1/ingest/test",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_ingest_data_when_ok(
    client: TestClient, user_header_token, ingest_service_mock
):

    response = client.post(
        "/api/v1/ingest/test",
        files={
            "new_data": open(
                os.path.join(
                    "tests", "unit_tests", "routers", "ingest", "test_bulk_data.json"
                ),
                "rb",
            )
        },
        headers=user_header_token,
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {
        "collections": ["test.new.collection.0", "test.new.collection.1"],
        "families": ["test.new.family.0", "test.new.family.1"],
        "documents": ["test.new.document.0", "test.new.document.1"],
        "events": ["test.new.event.0", "test.new.event.1"],
    }


def test_ingest_when_data_invalid(
    client: TestClient,
    user_header_token,
    corpus_service_mock,
    basic_s3_client,
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


def test_ingest_when_no_data(
    client: TestClient,
    user_header_token,
    collection_repo_mock,
    corpus_service_mock,
    basic_s3_client,
):
    test_data = json.dumps({}).encode("utf-8")
    test_data_file = io.BytesIO(test_data)
    response = client.post(
        "/api/v1/ingest/test",
        files={"new_data": test_data_file},
        headers=user_header_token,
    )

    assert collection_repo_mock.create.call_count == 0

    assert response.status_code == status.HTTP_204_NO_CONTENT


@patch("app.service.ingest._exists_in_db", Mock(return_value=False))
def test_ingest_data_when_db_error(
    client: TestClient, user_header_token, ingest_service_mock
):
    ingest_service_mock.throw_repository_error = True

    response = client.post(
        "/api/v1/ingest/test",
        files={
            "new_data": open(
                os.path.join(
                    "tests", "unit_tests", "routers", "ingest", "test_bulk_data.json"
                ),
                "rb",
            )
        },
        headers=user_header_token,
    )

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json().get("detail") == "bad repo"
