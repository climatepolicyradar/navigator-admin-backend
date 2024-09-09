from datetime import datetime

import pytest

import app.service.ingest as ingest_service
from app.errors import RepositoryError, ValidationError


def test_ingest_when_ok(
    corpus_repo_mock,
    geography_repo_mock,
    db_client_metadata_mock,
    collection_repo_mock,
    family_repo_mock,
    document_repo_mock,
    event_repo_mock,
):
    test_data = {
        "collections": [
            {
                "import_id": "",
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
                "collections": [],
            },
        ],
        "documents": [
            {
                "import_id": "test.new.document.0",
                "family_import_id": "test.new.family.0",
                "variant_name": "Original Language",
                "metadata": {"color": ["blue"]},
                "events": [],
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

    assert ingest_service.import_data(test_data, "test") == {
        "collections": ["test.new.collection.0"],
        "families": ["created"],
        "documents": ["test.new.doc.0"],
        "events": ["test.new.event.0"],
    }


def test_ingest_when_db_error(corpus_repo_mock, collection_repo_mock):
    collection_repo_mock.throw_repository_error = True

    test_data = {
        "collections": [
            {
                "import_id": "",
                "title": "Test title",
                "description": "Test description",
            }
        ]
    }

    with pytest.raises(RepositoryError) as e:
        ingest_service.import_data(test_data, "test")
    assert e.value.message == "bad collection repo"


def test_save_collections_when_import_id_wrong_format(corpus_repo_mock):
    invalid_import_id = "invalid"
    test_data = [
        {
            "import_id": invalid_import_id,
            "title": "Test title",
            "description": "Test description",
        },
    ]

    with pytest.raises(ValidationError) as e:
        ingest_service.save_collections(test_data, "test")
    expected_msg = "The import id invalid is invalid!"
    assert e.value.message == expected_msg


def test_ingest_families_when_import_id_wrong_format(
    corpus_repo_mock, geography_repo_mock, db_client_metadata_mock
):
    invalid_import_id = "invalid"
    test_data = [
        {
            "import_id": invalid_import_id,
            "title": "Test",
            "summary": "Test",
            "geography": "Test",
            "category": "UNFCCC",
            "metadata": {"color": ["blue"], "size": [""]},
            "collections": [],
        },
    ]

    with pytest.raises(ValidationError) as e:
        ingest_service.save_families(test_data, "test")
    expected_msg = "The import id invalid is invalid!"
    assert e.value.message == expected_msg


def test_ingest_families_when_geography_invalid(corpus_repo_mock, geography_repo_mock):
    geography_repo_mock.error = True
    test_data = [
        {
            "import_id": "test.new.family.0",
            "title": "Test",
            "summary": "Test",
            "geography": "Invalid",
            "category": "Test",
            "metadata": {},
            "collections": [],
        },
    ]

    with pytest.raises(ValidationError) as e:
        ingest_service.save_families(test_data, "test")
    expected_msg = "The geography value Invalid is invalid!"
    assert e.value.message == expected_msg


def test_ingest_families_when_category_invalid(corpus_repo_mock, geography_repo_mock):
    test_data = [
        {
            "import_id": "test.new.family.0",
            "title": "Test",
            "summary": "Test",
            "geography": "Test",
            "category": "Test",
            "metadata": {},
            "collections": [],
        },
    ]

    with pytest.raises(ValidationError) as e:
        ingest_service.save_families(test_data, "test")
    expected_msg = "Test is not a valid FamilyCategory"
    assert e.value.message == expected_msg


def test_ingest_families_when_corpus_invalid(corpus_repo_mock):
    corpus_repo_mock.valid = False

    test_data = [
        {
            "import_id": "test.new.family.0",
            "title": "Test",
            "summary": "Test",
            "geography": "Test",
            "category": "Test",
            "metadata": {},
            "collections": [],
        },
    ]

    with pytest.raises(ValidationError) as e:
        ingest_service.save_families(test_data, "test")
    expected_msg = "Corpus 'test' not found"
    assert e.value.message == expected_msg


def test_ingest_families_when_collection_ids_invalid(
    corpus_repo_mock, geography_repo_mock
):
    test_data = [
        {
            "import_id": "test.new.family.0",
            "title": "Test",
            "summary": "Test",
            "geography": "Test",
            "category": "UNFCCC",
            "metadata": {},
            "collections": ["invalid"],
        },
    ]

    with pytest.raises(ValidationError) as e:
        ingest_service.save_families(test_data, "test")
    expected_msg = "The import ids are invalid: ['invalid']"
    assert e.value.message == expected_msg


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


def test_ingest_families_when_metadata_not_found(
    corpus_repo_mock, geography_repo_mock, collection_repo_mock, db_client_metadata_mock
):
    db_client_metadata_mock.bad_taxonomy = True

    test_data = [
        {
            "import_id": "test.new.family.0",
            "title": "Test",
            "summary": "Test",
            "geography": "Test",
            "category": "UNFCCC",
            "metadata": {},
            "collections": ["id.does.not.exist"],
        },
    ]

    with pytest.raises(ValidationError) as e:
        ingest_service.save_families(test_data, "test")
    expected_msg = "No taxonomy found for corpus"
    assert e.value.message == expected_msg


def test_ingest_families_when_metadata_invalid(
    corpus_repo_mock, geography_repo_mock, collection_repo_mock, db_client_metadata_mock
):
    test_data = [
        {
            "import_id": "test.new.family.0",
            "title": "Test",
            "summary": "Test",
            "geography": "Test",
            "category": "UNFCCC",
            "metadata": {},
            "collections": ["id.does.not.exist"],
        },
    ]

    with pytest.raises(ValidationError) as e:
        ingest_service.save_families(test_data, "test")
    expected_msg = "Metadata validation failed: Missing metadata keys:"
    assert expected_msg in e.value.message


def test_save_documents_when_variant_empty():
    test_data = [
        {
            "import_id": "test.new.document.0",
            "family_import_id": "test.new.family.0",
            "variant_name": "",
            "metadata": {},
            "events": [],
            "title": "",
            "user_language_name": "",
        },
    ]

    with pytest.raises(ValidationError) as e:
        ingest_service.save_documents(test_data, "test")
    assert e.value.message == "Variant name is empty"


def test_ingest_documents_when_metadata_invalid(db_client_metadata_mock):
    test_data = [
        {
            "import_id": "test.new.document.0",
            "family_import_id": "test.new.family.0",
            "variant_name": None,
            "metadata": {},
            "events": [],
            "title": "",
            "user_language_name": "",
        },
    ]

    with pytest.raises(ValidationError) as e:
        ingest_service.save_documents(test_data, "test")
    expected_msg = "Metadata validation failed: Missing metadata keys:"
    assert expected_msg in e.value.message


def test_validate_entity_relationships_when_no_family_matching_document():
    fam_import_id = "test.new.family.0"
    test_data = {
        "documents": [
            {"import_id": "test.new.document.0", "family_import_id": fam_import_id}
        ]
    }

    with pytest.raises(ValidationError) as e:
        ingest_service.validate_entity_relationships(test_data)
    assert e.value.message == f"No family with id ['{fam_import_id}'] found"


def test_ingest_documents_when_no_family():
    fam_import_id = "test.new.family.0"
    test_data = {
        "documents": [
            {"import_id": "test.new.document.0", "family_import_id": fam_import_id}
        ]
    }

    with pytest.raises(ValidationError) as e:
        ingest_service.import_data(test_data, "test")
    assert e.value.message == f"No family with id ['{fam_import_id}'] found"


def test_ingest_documents_when_import_id_wrong_format():
    invalid_import_id = "invalid"
    test_data = [
        {
            "import_id": invalid_import_id,
            "family_import_id": "test.new.family.0",
            "variant_name": "Original Language",
            "metadata": {"color": ["blue"]},
            "events": [],
            "title": "",
            "source_url": None,
            "user_language_name": "",
        }
    ]

    with pytest.raises(ValidationError) as e:
        ingest_service.save_documents(test_data, "test")
    expected_msg = f"The import id {invalid_import_id} is invalid!"
    assert e.value.message == expected_msg


def test_ingest_documents_when_family_import_id_wrong_format():
    invalid_family_import_id = "invalid"
    test_data = [
        {
            "import_id": "test.new.document.0",
            "family_import_id": invalid_family_import_id,
            "variant_name": "Original Language",
            "metadata": {"color": ["blue"]},
            "events": [],
            "title": "",
            "source_url": None,
            "user_language_name": "",
        }
    ]

    with pytest.raises(ValidationError) as e:
        ingest_service.save_documents(test_data, "test")
    expected_msg = f"The import id {invalid_family_import_id} is invalid!"
    assert e.value.message == expected_msg


def test_ingest_events_when_import_id_wrong_format():
    invalid_import_id = "invalid"
    test_data = [
        {
            "import_id": invalid_import_id,
            "family_import_id": "test.new.family.0",
            "event_title": "Test",
            "date": datetime.now(),
            "event_type_value": "Amended",
        }
    ]

    with pytest.raises(ValidationError) as e:
        ingest_service.save_events(test_data)
    expected_msg = f"The import id {invalid_import_id} is invalid!"
    assert e.value.message == expected_msg


def test_ingest_events_when_family_import_id_wrong_format():
    invalid_import_id = "invalid"
    test_data = [
        {
            "import_id": "test.new.event.0",
            "family_import_id": invalid_import_id,
            "event_title": "Test",
            "date": datetime.now(),
            "event_type_value": "Amended",
        }
    ]

    with pytest.raises(ValidationError) as e:
        ingest_service.save_events(test_data)
    expected_msg = f"The import id {invalid_import_id} is invalid!"
    assert e.value.message == expected_msg
