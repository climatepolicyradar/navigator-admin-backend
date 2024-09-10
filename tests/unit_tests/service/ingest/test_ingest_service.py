from datetime import datetime

import pytest

import app.service.ingest as ingest_service
from app.errors import RepositoryError, ValidationError


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
                "geography": "Test",
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
        "families": ["created"],
        "documents": ["test.new.doc.0"],
        "events": ["test.new.event.0"],
    } == ingest_service.import_data(test_data, "test")


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


# TODO: Uncomment when implementing feature/pdct-1402-validate-collection-exists-before-creating-family
# def test_ingest_families_when_collection_ids_do_not_exist(
#     corpus_repo_mock, geography_repo_mock, collection_repo_mock
# ):
#     collection_repo_mock.missing = True

#     test_data = {
#         "families": [
#             {
#                 "import_id": "test.new.family.0",
#                 "title": "Test",
#                 "summary": "Test",
#                 "geography": "Test",
#                 "category": "UNFCCC",
#                 "metadata": {},
#                 "collections": ["id.does.not.exist"],
#             },
#         ],
#     }
#     with pytest.raises(ValidationError) as e:
#         ingest_service.import_data(test_data, "test")
#     expected_msg = "One or more of the collections to update does not exist"
#     assert e.value.message == expected_msg


def test_save_documents_when_data_invalid(validation_service_mock):
    validation_service_mock.throw_validation_error = True

    test_data = [{"import_id": "invalid"}]

    with pytest.raises(ValidationError) as e:
        ingest_service.save_documents(test_data, "test")
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
    assert f"No family with id ['{fam_import_id}'] found" == e.value.message


def test_save_documents_when_no_family():
    fam_import_id = "test.new.family.0"
    test_data = {
        "documents": [
            {"import_id": "test.new.document.0", "family_import_id": fam_import_id}
        ]
    }

    with pytest.raises(ValidationError) as e:
        ingest_service.import_data(test_data, "test")
    assert f"No family with id ['{fam_import_id}'] found" == e.value.message


def test_save_events_when_data_invalid(validation_service_mock):
    validation_service_mock.throw_validation_error = True

    test_data = [{"import_id": "imvalid"}]

    with pytest.raises(ValidationError) as e:
        ingest_service.save_events(test_data, "test")
    assert "Error" == e.value.message
