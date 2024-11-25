import logging

from db_client.models.dfce import FamilyEvent
from db_client.models.dfce.collection import Collection
from db_client.models.dfce.family import Family, FamilyDocument
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.orm import Session

from tests.helpers.ingest import (
    build_json_file,
    default_collection,
    default_document,
    default_event,
    default_family,
)


def create_input_json_with_two_of_each_entity():
    return build_json_file(
        {
            "collections": [
                default_collection,
                {**default_collection, "import_id": "test.new.collection.1"},
            ],
            "families": [
                default_family,
                {
                    **default_family,
                    "import_id": "test.new.family.1",
                    "collections": ["test.new.collection.1"],
                },
            ],
            "documents": [
                default_document,
                {
                    **default_document,
                    "import_id": "test.new.document.1",
                    "family_import_id": "test.new.family.1",
                },
            ],
            "events": [
                default_event,
                {
                    **default_event,
                    "import_id": "test.new.event.1",
                    "family_import_id": "test.new.family.1",
                },
            ],
        }
    )


def test_ingest_when_ok(data_db: Session, client: TestClient, superuser_header_token):
    input_json = create_input_json_with_two_of_each_entity()

    response = client.post(
        "/api/v1/ingest/UNFCCC.corpus.i00000001.n0000",
        files={"new_data": input_json},
        headers=superuser_header_token,
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


def test_import_data_rollback(
    caplog,
    data_db: Session,
    client: TestClient,
    superuser_header_token,
    rollback_collection_repo,
):
    input_json = create_input_json_with_two_of_each_entity()

    with caplog.at_level(logging.ERROR):
        response = client.post(
            "/api/v1/ingest/UNFCCC.corpus.i00000001.n0000",
            files={"new_data": input_json},
            headers=superuser_header_token,
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


def test_ingest_idempotency(
    caplog,
    data_db: Session,
    client: TestClient,
    superuser_header_token,
):
    input_json = build_json_file(
        {
            "collections": [default_collection],
            "families": [default_family],
            "documents": [
                {**default_document, "import_id": f"test.new.document.{i}"}
                for i in range(1001)
            ],
            "events": [default_event],
        }
    )

    with caplog.at_level(logging.ERROR):
        first_response = client.post(
            "/api/v1/ingest/UNFCCC.corpus.i00000001.n0000",
            files={"new_data": input_json},
            headers=superuser_header_token,
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
            files={"new_data": input_json},
            headers=superuser_header_token,
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


def test_generates_unique_slugs_for_documents_with_identical_titles(
    caplog,
    data_db: Session,
    client: TestClient,
    superuser_header_token,
):
    """
    This test ensures that given multiple documents with the same title a unique slug
    is generated for each and thus the documents can be saved to the DB at the end
    of bulk import. However, the current length of the suffix added to the slug
    to ensure uniqueness (6), means that the likelihood of a collision is extremely low.
    """

    input_json = build_json_file(
        {
            "families": [{**default_family, "collections": []}],
            "documents": [
                {**default_document, "import_id": f"test.new.document.{i}"}
                for i in range(1000)
            ],
        }
    )

    with caplog.at_level(logging.ERROR):
        response = client.post(
            "/api/v1/ingest/UNFCCC.corpus.i00000001.n0000",
            files={"new_data": input_json},
            headers=superuser_header_token,
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.json() == {
            "message": "Bulk import request accepted. Check Cloudwatch logs for result."
        }

    assert (
        "Created"
        == data_db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == "test.new.document.999")
        .one_or_none()
        .document_status
    )


def test_ingest_when_corpus_import_id_invalid(
    caplog,
    data_db: Session,
    client: TestClient,
    superuser_header_token,
):
    invalid_corpus = "test"
    input_json = create_input_json_with_two_of_each_entity()

    with caplog.at_level(logging.ERROR):
        response = client.post(
            f"/api/v1/ingest/{invalid_corpus}",
            files={"new_data": input_json},
            headers=superuser_header_token,
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.json() == {
            "message": "Bulk import request accepted. Check Cloudwatch logs for result."
        }

    assert f"No organisation associated with corpus {invalid_corpus}" in caplog.text


def test_ingest_events_when_event_type_invalid(
    caplog,
    data_db: Session,
    client: TestClient,
    superuser_header_token,
):

    input_json = build_json_file(
        {
            "families": [{**default_family, "collections": []}],
            "documents": [default_document],
            "events": [{**default_event, "event_type_value": "Invalid"}],
        }
    )

    with caplog.at_level(logging.ERROR):
        response = client.post(
            "/api/v1/ingest/UNFCCC.corpus.i00000001.n0000",
            files={"new_data": input_json},
            headers=superuser_header_token,
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.json() == {
            "message": "Bulk import request accepted. Check Cloudwatch logs for result."
        }

    assert (
        "Metadata validation failed: Invalid value '['Invalid']' for metadata key 'event_type'"
        in caplog.text
    )


def test_ingest_when_not_authorised(client: TestClient, data_db: Session):
    response = client.post(
        "/api/v1/ingest/UNFCCC.corpus.i00000001.n0000",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_ingest_admin_non_super(
    client: TestClient, data_db: Session, admin_user_header_token
):
    response = client.post(
        "/api/v1/ingest/UNFCCC.corpus.i00000001.n0000",
        headers=admin_user_header_token,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert data["detail"] == "User admin@cpr.org is not authorised to CREATE an INGEST"


def test_ingest_non_super_non_admin(
    client: TestClient, data_db: Session, user_header_token
):
    response = client.post(
        "/api/v1/ingest/UNFCCC.corpus.i00000001.n0000",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert data["detail"] == "User cclw@cpr.org is not authorised to CREATE an INGEST"
