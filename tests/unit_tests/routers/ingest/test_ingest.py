"""
Tests the route for bulk import of data.

This uses service mocks and ensures the endpoint calls into each service.
"""

import io
import json
import os
from unittest.mock import Mock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.api.api_v1.routers.ingest import validate_entity_relationships
from app.errors import ValidationError


def test_ingest_when_not_authenticated(client: TestClient):
    response = client.post(
        "/api/v1/ingest/test",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@patch("app.service.ingest._exists_in_db", Mock(return_value=False))
def test_ingest_data_when_ok(
    client: TestClient,
    user_header_token,
    collection_repo_mock,
    geography_repo_mock,
    corpus_repo_mock,
    family_repo_mock,
    document_repo_mock,
    db_client_metadata_mock,
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
        "message": "Bulk import request accepted. Check Cloudwatch logs for result."
    }


def test_ingest_when_no_data(
    client: TestClient, user_header_token, collection_repo_mock, corpus_service_mock
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


def test_ingest_documents_when_no_family(client: TestClient, user_header_token):
    fam_import_id = "test.new.family.0"
    test_data = json.dumps(
        {
            "documents": [
                {"import_id": "test.new.document.0", "family_import_id": fam_import_id}
            ]
        }
    ).encode("utf-8")
    test_data_file = io.BytesIO(test_data)

    response = client.post(
        "/api/v1/ingest/test",
        files={"new_data": test_data_file},
        headers=user_header_token,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json().get("detail") == f"No entity with id {fam_import_id} found"


def test_validate_entity_relationships_when_no_family_matching_document():
    fam_import_id = "test.new.family.0"
    test_data = {
        "documents": [
            {"import_id": "test.new.document.0", "family_import_id": fam_import_id}
        ]
    }

    with pytest.raises(ValidationError) as e:
        validate_entity_relationships(test_data)
    assert f"No entity with id {fam_import_id} found" == e.value.message


def test_validate_entity_relationships_when_no_family_matching_event():
    fam_import_id = "test.new.family.0"
    test_data = {
        "events": [{"import_id": "test.new.event.0", "family_import_id": fam_import_id}]
    }

    with pytest.raises(ValidationError) as e:
        validate_entity_relationships(test_data)
    assert f"No entity with id {fam_import_id} found" == e.value.message


def test_validate_entity_relationships_when_no_collection_matching_family():
    coll_import_id = "test.new.collection.0"
    test_data = {
        "families": [{"import_id": "test.new.event.0", "collections": [coll_import_id]}]
    }

    with pytest.raises(ValidationError) as e:
        validate_entity_relationships(test_data)
    assert f"No entity with id {coll_import_id} found" == e.value.message
