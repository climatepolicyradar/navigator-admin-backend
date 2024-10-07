import logging

from db_client.models.dfce.collection import Collection
from db_client.models.dfce.family import FamilyDocument
from sqlalchemy.orm import Session

from app.service.ingest import import_data
from tests.integration_tests.setup_db import setup_db


def test_import_data_rollback(caplog, data_db: Session, rollback_collection_repo):
    setup_db(data_db)

    with caplog.at_level(logging.ERROR):
        import_data(
            {
                "collections": [
                    {
                        "import_id": "test.new.collection.0",
                        "title": "Test title",
                        "description": "Test description",
                    }
                ]
            },
            "UNFCCC.corpus.i00000001.n0000",
        )

    assert "Rolling back transaction due to the following error:" in caplog.text
    actual_collection = (
        data_db.query(Collection)
        .filter(Collection.import_id == "test.new.collection.0")
        .one_or_none()
    )
    assert actual_collection is None


def test_ingest_idempotency(caplog, data_db: Session):
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

    with caplog.at_level(logging.ERROR):
        import_data(
            test_data,
            "UNFCCC.corpus.i00000001.n0000",
        )

    assert (
        not data_db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == "test.new.document.1000")
        .one_or_none()
    )

    with caplog.at_level(logging.ERROR):
        import_data(
            test_data,
            "UNFCCC.corpus.i00000001.n0000",
        )

    assert (
        "test.new.document.1000"
        == data_db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == "test.new.document.1000")
        .one_or_none()
        .import_id
    )


def test_ingest_when_corpus_import_id_invalid(caplog, data_db: Session):
    invalid_corpus = "test"

    with caplog.at_level(logging.ERROR):
        import_data(
            {
                "collections": [
                    {
                        "import_id": "test.new.collection.0",
                        "title": "Test title",
                        "description": "Test description",
                    },
                ]
            },
            invalid_corpus,
        )

    assert f"No organisation associated with corpus {invalid_corpus}" in caplog.text


def test_ingest_events_when_event_type_invalid(
    caplog,
    data_db: Session,
):
    with caplog.at_level(logging.ERROR):
        import_data(
            {
                "events": [
                    {
                        "import_id": "test.new.event.0",
                        "family_import_id": "test.new.family.0",
                        "event_title": "Test",
                        "date": "2024-01-01",
                        "event_type_value": "Invalid",
                    }
                ]
            },
            "UNFCCC.corpus.i00000001.n0000",
        )

    assert "Event type ['Invalid'] is invalid!" in caplog.text
