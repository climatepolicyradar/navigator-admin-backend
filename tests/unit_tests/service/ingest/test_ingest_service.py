from datetime import datetime
from unittest.mock import Mock, patch

import pytest

import app.service.ingest as ingest_service
from app.errors import RepositoryError, ValidationError


@patch("app.service.ingest._exists_in_db", Mock(return_value=False))
def test_ingest_when_ok(
    corpus_repo_mock,
    geography_repo_mock,
    collection_repo_mock,
    family_repo_mock,
    document_repo_mock,
    event_repo_mock,
    validation_service_mock,
):
    test_data = {
        "collections": [
            {
                "import_id": "test.new.collection.0",
                "title": "Test title",
                "description": "Test description",
            },
        ],
        "families": [
            {
                "import_id": "test.new.family.0",
                "title": "Test",
                "summary": "Test",
                "geographies": ["Test"],
                "category": "UNFCCC",
                "metadata": {"color": ["blue"], "size": [""]},
                "collections": ["test.new.collection.0"],
            },
        ],
        "documents": [
            {
                "import_id": "test.new.document.0",
                "family_import_id": "test.new.family.0",
                "variant_name": "Original Language",
                "metadata": {"color": ["blue"]},
                "title": "",
                "source_url": None,
                "user_language_name": "",
            }
        ],
        "events": [
            {
                "import_id": "test.new.event.0",
                "family_import_id": "test.new.family.0",
                "event_title": "Test",
                "date": datetime.now(),
                "event_type_value": "Amended",
            }
        ],
    }

    assert {
        "collections": ["test.new.collection.0"],
        "families": ["test.new.family.0"],
        "documents": ["test.new.document.0"],
        "events": ["test.new.event.0"],
    } == ingest_service.import_data(test_data, "test")


@patch("app.service.ingest._exists_in_db", Mock(return_value=False))
def test_ingest_when_db_error(corpus_repo_mock, collection_repo_mock):
    collection_repo_mock.throw_repository_error = True

    test_data = {
        "collections": [
            {
                "import_id": "test.new.collection.0",
                "title": "Test title",
                "description": "Test description",
            }
        ]
    }

    with pytest.raises(RepositoryError) as e:
        ingest_service.import_data(test_data, "test")
    assert "bad collection repo" == e.value.message


def test_save_families_when_corpus_invalid(corpus_repo_mock, validation_service_mock):
    corpus_repo_mock.error = True

    test_data = [{"import_id": "test.new.family.0"}]

    with pytest.raises(ValidationError) as e:
        ingest_service.save_families(test_data, "test")
    assert "No organisation associated with corpus test" == e.value.message


def test_save_families_when_data_invalid(corpus_repo_mock, validation_service_mock):
    validation_service_mock.throw_validation_error = True
    test_data = [{"import_id": "invalid"}]

    with pytest.raises(ValidationError) as e:
        ingest_service.save_families(test_data, "test")
    assert "Error" == e.value.message


def test_save_documents_when_data_invalid(validation_service_mock):
    validation_service_mock.throw_validation_error = True

    test_data = [{"import_id": "invalid"}]

    with pytest.raises(ValidationError) as e:
        ingest_service.save_documents(test_data, "test")
    assert "Error" == e.value.message


@patch("app.service.ingest._exists_in_db", Mock(return_value=False))
def test_do_not_save_documents_over_ingest_limit(
    validation_service_mock, document_repo_mock, monkeypatch
):
    monkeypatch.setattr(ingest_service, "DOCUMENT_INGEST_LIMIT", 1)

    test_data = [
        {
            "import_id": "test.new.document.0",
            "family_import_id": "test.new.family.0",
            "variant_name": "Original Language",
            "metadata": {"color": ["blue"]},
            "title": "",
            "source_url": None,
            "user_language_name": "",
        },
        {
            "import_id": "test.new.document.1",
            "family_import_id": "test.new.family.1",
            "variant_name": "Original Language",
            "metadata": {"color": ["blue"]},
            "title": "",
            "source_url": None,
            "user_language_name": "",
        },
    ]

    saved_documents = ingest_service.save_documents(test_data, "test")
    assert ["test.new.document.0"] == saved_documents


def test_ingest_documents_when_no_family():
    fam_import_id = "test.new.family.0"
    test_data = {
        "documents": [
            {"import_id": "test.new.document.0", "family_import_id": fam_import_id}
        ]
    }

    with pytest.raises(ValidationError) as e:
        ingest_service.import_data(test_data, "test")
    assert f"No entity with id {fam_import_id} found" == e.value.message


def test_save_events_when_data_invalid(validation_service_mock):
    validation_service_mock.throw_validation_error = True

    test_data = [{"import_id": "invalid"}]

    with pytest.raises(ValidationError) as e:
        ingest_service.save_events(test_data, "test")
    assert "Error" == e.value.message


def test_validate_entity_relationships_when_no_family_matching_document():
    fam_import_id = "test.new.family.0"
    test_data = {
        "documents": [
            {"import_id": "test.new.document.0", "family_import_id": fam_import_id}
        ]
    }

    with pytest.raises(ValidationError) as e:
        ingest_service.validate_entity_relationships(test_data)
    assert f"No entity with id {fam_import_id} found" == e.value.message


def test_validate_entity_relationships_when_no_family_matching_event():
    fam_import_id = "test.new.family.0"
    test_data = {
        "events": [{"import_id": "test.new.event.0", "family_import_id": fam_import_id}]
    }

    with pytest.raises(ValidationError) as e:
        ingest_service.validate_entity_relationships(test_data)
    assert f"No entity with id {fam_import_id} found" == e.value.message


def test_validate_entity_relationships_when_no_collection_matching_family():
    coll_import_id = "test.new.collection.0"
    test_data = {
        "families": [{"import_id": "test.new.event.0", "collections": [coll_import_id]}]
    }

    with pytest.raises(ValidationError) as e:
        ingest_service.validate_entity_relationships(test_data)
    assert f"No entity with id {coll_import_id} found" == e.value.message
