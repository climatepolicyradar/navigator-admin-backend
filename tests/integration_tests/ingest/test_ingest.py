import io
import json
import os

from db_client.models.dfce import FamilyEvent
from db_client.models.dfce.collection import Collection
from db_client.models.dfce.family import Family, FamilyDocument
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.integration_tests.setup_db import setup_db


def test_ingest_when_ok(data_db: Session, client: TestClient, user_header_token):

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

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {
        "collections": expected_collection_import_ids,
        "families": expected_family_import_ids,
        "documents": expected_document_import_ids,
        "events": expected_event_import_ids,
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

    saved_events = (
        data_db.query(FamilyDocument)
        .filter(FamilyDocument.import_id.in_(expected_document_import_ids))
        .all()
    )

    assert len(saved_events) == 2
    for doc in saved_events:
        assert doc.import_id in expected_document_import_ids
        assert doc.family_import_id in expected_family_import_ids

    saved_events = (
        data_db.query(FamilyEvent)
        .filter(FamilyEvent.import_id.in_(expected_event_import_ids))
        .all()
    )

    assert len(saved_events) == 2
    for doc in saved_events:
        assert doc.import_id in expected_event_import_ids
        assert doc.family_import_id in expected_family_import_ids


def test_ingest_rollback(
    client: TestClient, data_db: Session, rollback_collection_repo, user_header_token
):
    setup_db(data_db)

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

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    actual_collection = (
        data_db.query(Collection)
        .filter(Collection.import_id == "test.new.collection.0")
        .one_or_none()
    )
    assert actual_collection is None


def test_ingest_idempotency(data_db: Session, client: TestClient, user_header_token):
    test_data = {
        "families": [
            {
                "import_id": "test.new.family.0",
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
                "family_import_id": "test.new.family.0",
                "metadata": {"role": ["MAIN"], "type": ["Law"]},
                "variant_name": "Original Language",
                "title": f"Document{i}",
                "user_language_name": "",
            }
            for i in range(1001)
        ],
    }

    test_json = json.dumps(test_data).encode("utf-8")
    test_data_file = io.BytesIO(test_json)

    response = client.post(
        "/api/v1/ingest/UNFCCC.corpus.i00000001.n0000",
        files={"new_data": test_data_file},
        headers=user_header_token,
    )

    assert ["test.new.family.0"] == response.json()["families"]
    assert "test.new.document.1000" not in response.json()["documents"]

    response = client.post(
        "/api/v1/ingest/UNFCCC.corpus.i00000001.n0000",
        files={"new_data": test_data_file},
        headers=user_header_token,
    )

    assert not response.json()["families"]
    assert ["test.new.document.1000"] == response.json()["documents"]


def test_ingest_when_corpus_import_id_invalid(
    data_db: Session, client: TestClient, user_header_token
):
    invalid_corpus = "test"
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

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json().get("detail")
        == f"No organisation associated with corpus {invalid_corpus}"
    )


def test_ingest_events_when_event_type_invalid(
    data_db: Session, client: TestClient, user_header_token
):
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

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json().get("detail") == "Event type ['Invalid'] is invalid!"
