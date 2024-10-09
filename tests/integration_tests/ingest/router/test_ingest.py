import os

from db_client.models.dfce import FamilyEvent
from db_client.models.dfce.collection import Collection
from db_client.models.dfce.family import Family, FamilyDocument
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


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
