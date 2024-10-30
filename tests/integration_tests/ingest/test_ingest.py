import io
import json
import logging
import os
from unittest.mock import patch

from db_client.models.dfce import FamilyEvent
from db_client.models.dfce.collection import Collection
from db_client.models.dfce.family import Family, FamilyDocument
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.orm import Session

from tests.integration_tests.setup_db import setup_db


@patch.dict(os.environ, {"BULK_IMPORT_BUCKET": "test_bucket"})
def test_ingest_when_ok(
    data_db: Session, client: TestClient, user_header_token, basic_s3_client
):

    response = client.post(
        "/api/v1/ingest/UNFCCC.corpus.i00000001.n0000",
        files={
            "new_data": open(
                os.path.join(
                    "tests", "integration_tests", "ingest", "test_bulk_data.json"
                ),
                "rb",
            )
        },
        headers=user_header_token,
    )

    expected_collection_import_ids = ["test.new.collection.0", "test.new.collection.1"]
    expected_family_import_ids = ["test.new.family.0", "test.new.family.1"]
    expected_document_import_ids = ["test.new.document.0", "test.new.document.1"]
    expected_event_import_ids = ["test.new.event.0", "test.new.event.1"]

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == {
        "message": "Bulk import request accepted. Check Cloudwatch logs for result."
    }

    saved_collections = (
        data_db.query(Collection)
        .filter(Collection.import_id.in_(expected_collection_import_ids))
        .all()
    )

    assert len(saved_collections) == 2
    for coll in saved_collections:
        assert coll.import_id in expected_collection_import_ids

    saved_families = (
        data_db.query(Family)
        .filter(Family.import_id.in_(expected_family_import_ids))
        .all()
    )

    assert len(saved_families) == 2
    for fam in saved_families:
        assert fam.import_id in expected_family_import_ids

    saved_documents = (
        data_db.query(FamilyDocument)
        .filter(FamilyDocument.import_id.in_(expected_document_import_ids))
        .all()
    )

    assert len(saved_documents) == 2
    for doc in saved_documents:
        assert doc.import_id in expected_document_import_ids
        assert doc.family_import_id in expected_family_import_ids

    saved_events = (
        data_db.query(FamilyEvent)
        .filter(FamilyEvent.import_id.in_(expected_event_import_ids))
        .all()
    )

    assert len(saved_events) == 2
    for ev in saved_events:
        assert ev.import_id in expected_event_import_ids
        assert ev.family_import_id in expected_family_import_ids


@patch.dict(os.environ, {"BULK_IMPORT_BUCKET": "test_bucket"})
def test_import_data_rollback(
    caplog,
    data_db: Session,
    client: TestClient,
    user_header_token,
    rollback_collection_repo,
    basic_s3_client,
):
    setup_db(data_db)

    with caplog.at_level(logging.ERROR):
        response = client.post(
            "/api/v1/ingest/UNFCCC.corpus.i00000001.n0000",
            files={
                "new_data": open(
                    os.path.join(
                        "tests", "integration_tests", "ingest", "test_bulk_data.json"
                    ),
                    "rb",
                )
            },
            headers=user_header_token,
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.json() == {
            "message": "Bulk import request accepted. Check Cloudwatch logs for result."
        }

    assert "Rolling back transaction due to the following error:" in caplog.text
    actual_collection = (
        data_db.query(Collection)
        .filter(Collection.import_id == "test.new.collection.0")
        .one_or_none()
    )
    assert actual_collection is None


@patch.dict(os.environ, {"BULK_IMPORT_BUCKET": "test_bucket"})
def test_ingest_idempotency(
    caplog, data_db: Session, client: TestClient, user_header_token, basic_s3_client
):
    family_import_id = "test.new.family.0"
    event_import_id = "test.new.event.0"
    collection_import_id = "test.new.collection.0"
    test_data = {
        "collections": [
            {
                "import_id": collection_import_id,
                "title": "Test title",
                "description": "Test description",
            },
        ],
        "families": [
            {
                "import_id": family_import_id,
                "title": "Test",
                "summary": "Test",
                "geographies": ["South Asia"],
                "category": "UNFCCC",
                "metadata": {"author_type": ["Non-Party"], "author": ["Test"]},
                "collections": [collection_import_id],
            }
        ],
        "documents": [
            {
                "import_id": f"test.new.document.{i}",
                "family_import_id": family_import_id,
                "metadata": {"role": ["MAIN"], "type": ["Law"]},
                "variant_name": "Original Language",
                "title": f"Document{i}",
                "user_language_name": "",
            }
            for i in range(1001)
        ],
        "events": [
            {
                "import_id": event_import_id,
                "family_import_id": family_import_id,
                "event_title": "Test",
                "date": "2024-01-01",
                "event_type_value": "Amended",
            }
        ],
    }
    test_json = json.dumps(test_data).encode("utf-8")
    test_data_file = io.BytesIO(test_json)

    with caplog.at_level(logging.ERROR):
        first_response = client.post(
            "/api/v1/ingest/UNFCCC.corpus.i00000001.n0000",
            files={"new_data": test_data_file},
            headers=user_header_token,
        )

        assert first_response.status_code == status.HTTP_202_ACCEPTED
        assert first_response.json() == {
            "message": "Bulk import request accepted. Check Cloudwatch logs for result."
        }

    assert (
        "Created"
        == data_db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == "test.new.document.999")
        .one_or_none()
        .document_status
    )

    assert (
        not data_db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == "test.new.document.1000")
        .one_or_none()
    )

    # simulating pipeline ingest
    data_db.execute(
        update(FamilyDocument)
        .where(FamilyDocument.import_id == "test.new.document.999")
        .values(document_status="Published")
    )

    with caplog.at_level(logging.ERROR):
        second_response = client.post(
            "/api/v1/ingest/UNFCCC.corpus.i00000001.n0000",
            files={"new_data": test_json},
            headers=user_header_token,
        )

        assert second_response.status_code == status.HTTP_202_ACCEPTED
        assert second_response.json() == {
            "message": "Bulk import request accepted. Check Cloudwatch logs for result."
        }

    # checking that subsequent bulk import does not change the status
    assert (
        "Published"
        == data_db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == "test.new.document.999")
        .one_or_none()
        .document_status
    )

    assert (
        "Created"
        == data_db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == "test.new.document.1000")
        .one_or_none()
        .document_status
    )


@patch.dict(os.environ, {"BULK_IMPORT_BUCKET": "test_bucket"})
def test_generates_unique_slugs_for_documents_with_identical_titles(
    caplog, data_db: Session, client: TestClient, user_header_token, basic_s3_client
):
    """
    This test ensures that given multiple documents with the same title a unique slug
    is generated for each and thus the documents can be saved to the DB at the end
    of bulk import. However, the current length of the suffix added to the slug
    to ensure uniqueness (6), means that the likelihood of a collision is extremely low.
    """
    family_import_id = "test.new.family.0"
    test_data = {
        "collections": [],
        "families": [
            {
                "import_id": family_import_id,
                "title": "Test",
                "summary": "Test",
                "geographies": ["South Asia"],
                "category": "UNFCCC",
                "metadata": {"author_type": ["Non-Party"], "author": ["Test"]},
                "collections": [],
            }
        ],
        "documents": [
            {
                "import_id": f"test.new.document.{i}",
                "family_import_id": family_import_id,
                "metadata": {"role": ["MAIN"], "type": ["Law"]},
                "variant_name": "Original Language",
                "title": "Project Document",
                "user_language_name": "",
            }
            for i in range(1000)
        ],
        "events": [],
    }
    test_json = json.dumps(test_data).encode("utf-8")
    test_data_file = io.BytesIO(test_json)

    with caplog.at_level(logging.ERROR):
        first_response = client.post(
            "/api/v1/ingest/UNFCCC.corpus.i00000001.n0000",
            files={"new_data": test_data_file},
            headers=user_header_token,
        )

        assert first_response.status_code == status.HTTP_202_ACCEPTED
        assert first_response.json() == {
            "message": "Bulk import request accepted. Check Cloudwatch logs for result."
        }

    assert (
        "Created"
        == data_db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == "test.new.document.999")
        .one_or_none()
        .document_status
    )


@patch.dict(os.environ, {"BULK_IMPORT_BUCKET": "test_bucket"})
def test_ingest_when_corpus_import_id_invalid(
    caplog, data_db: Session, client: TestClient, user_header_token, basic_s3_client
):
    invalid_corpus = "test"

    with caplog.at_level(logging.ERROR):
        response = client.post(
            f"/api/v1/ingest/{invalid_corpus}",
            files={
                "new_data": open(
                    os.path.join(
                        "tests", "integration_tests", "ingest", "test_bulk_data.json"
                    ),
                    "rb",
                )
            },
            headers=user_header_token,
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.json() == {
            "message": "Bulk import request accepted. Check Cloudwatch logs for result."
        }

    assert f"No organisation associated with corpus {invalid_corpus}" in caplog.text


@patch.dict(os.environ, {"BULK_IMPORT_BUCKET": "test_bucket"})
def test_ingest_events_when_event_type_invalid(
    caplog, data_db: Session, client: TestClient, user_header_token, basic_s3_client
):
    with caplog.at_level(logging.ERROR):
        response = client.post(
            "/api/v1/ingest/UNFCCC.corpus.i00000001.n0000",
            files={
                "new_data": open(
                    os.path.join(
                        "tests",
                        "integration_tests",
                        "ingest",
                        "test_bulk_data_with_invalid_event_type.json",
                    ),
                    "rb",
                )
            },
            headers=user_header_token,
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.json() == {
            "message": "Bulk import request accepted. Check Cloudwatch logs for result."
        }

    assert "Event type ['Invalid'] is invalid!" in caplog.text
