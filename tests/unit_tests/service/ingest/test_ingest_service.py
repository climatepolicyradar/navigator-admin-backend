import pytest

import app.service.ingest as ingest_service
from app.errors import ValidationError


def test_ingest_collections_when_import_id_wrong_format(corpus_repo_mock):

    invalid_import_id = "invalid"
    test_data = {
        "collections": [
            {
                "import_id": invalid_import_id,
                "title": "Test title",
                "description": "Test description",
            },
        ],
        "families": [],
    }

    with pytest.raises(ValidationError) as e:
        ingest_service.import_data(test_data, "test")
    expected_msg = "The import id invalid is invalid!"
    assert e.value.message == expected_msg


def test_ingest_families_when_geography_invalid(corpus_repo_mock, geography_repo_mock):
    geography_repo_mock.error = True
    test_data = {
        "families": [
            {
                "import_id": "test.new.family.0",
                "title": "Test",
                "summary": "Test",
                "geography": "Invalid",
                "category": "Test",
                "metadata": {},
                "collections": [],
                "events": [],
                "documents": [],
            },
        ],
    }
    with pytest.raises(ValidationError) as e:
        ingest_service.import_data(test_data, "test")
    expected_msg = "The geography value Invalid is invalid!"
    assert e.value.message == expected_msg


def test_ingest_families_when_category_invalid(corpus_repo_mock, geography_repo_mock):
    test_data = {
        "families": [
            {
                "import_id": "test.new.family.0",
                "title": "Test",
                "summary": "Test",
                "geography": "Test",
                "category": "Test",
                "metadata": {},
                "collections": [],
                "events": [],
                "documents": [],
            },
        ],
    }
    with pytest.raises(ValidationError) as e:
        ingest_service.import_data(test_data, "test")
    expected_msg = "Test is not a valid FamilyCategory"
    assert e.value.message == expected_msg


def test_ingest_families_when_corpus_invalid(corpus_repo_mock):
    corpus_repo_mock.valid = False

    test_data = {
        "families": [
            {
                "import_id": "test.new.family.0",
                "title": "Test",
                "summary": "Test",
                "geography": "Test",
                "category": "Test",
                "metadata": {},
                "collections": [],
                "events": [],
                "documents": [],
            },
        ],
    }
    with pytest.raises(ValidationError) as e:
        ingest_service.import_data(test_data, "test")
    expected_msg = "Corpus 'test' not found"
    assert e.value.message == expected_msg


def test_ingest_families_when_collection_ids_invalid(
    corpus_repo_mock, geography_repo_mock
):
    test_data = {
        "families": [
            {
                "import_id": "test.new.family.0",
                "title": "Test",
                "summary": "Test",
                "geography": "Test",
                "category": "UNFCCC",
                "metadata": {},
                "collections": ["invalid"],
                "events": [],
                "documents": [],
            },
        ],
    }
    with pytest.raises(ValidationError) as e:
        ingest_service.import_data(test_data, "test")
    expected_msg = "The import ids are invalid: ['invalid']"
    assert e.value.message == expected_msg


def test_ingest_families_when_collection_ids_do_not_exist(
    corpus_repo_mock, geography_repo_mock, collection_repo_mock
):
    collection_repo_mock.missing = True

    test_data = {
        "families": [
            {
                "import_id": "test.new.family.0",
                "title": "Test",
                "summary": "Test",
                "geography": "Test",
                "category": "UNFCCC",
                "metadata": {},
                "collections": ["id.does.not.exist"],
                "events": [],
                "documents": [],
            },
        ],
    }
    with pytest.raises(ValidationError) as e:
        ingest_service.import_data(test_data, "test")
    expected_msg = "One or more of the collections to update does not exist"
    assert e.value.message == expected_msg


def test_ingest_families_when_metadata_not_found(
    corpus_repo_mock, geography_repo_mock, collection_repo_mock, db_client_metadata_mock
):
    db_client_metadata_mock.bad_taxonomy = True

    test_data = {
        "families": [
            {
                "import_id": "test.new.family.0",
                "title": "Test",
                "summary": "Test",
                "geography": "Test",
                "category": "UNFCCC",
                "metadata": {},
                "collections": ["id.does.not.exist"],
                "events": [],
                "documents": [],
            },
        ],
    }
    with pytest.raises(ValidationError) as e:
        ingest_service.import_data(test_data, "test")
    expected_msg = "No taxonomy found for corpus"
    assert e.value.message == expected_msg
