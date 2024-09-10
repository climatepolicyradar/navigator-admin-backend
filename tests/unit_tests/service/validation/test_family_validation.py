import pytest

import app.service.validation as validation_service
from app.errors import ValidationError


def test_validate_family_when_ok(corpus_repo_mock, db_client_metadata_mock):
    test_family = {
        "import_id": "test.new.family.0",
        "category": "UNFCCC",
        "metadata": {"color": ["blue"], "size": [""]},
        "collections": ["test.new.collection.0"],
    }

    validation_service.validate_family(test_family, "test")


def test_validate_family_when_import_id_invalid(corpus_repo_mock):
    invalid_import_id = "invalid"
    test_family = {
        "import_id": invalid_import_id,
    }

    with pytest.raises(ValidationError) as e:
        validation_service.validate_family(test_family, "test")
    assert "The import id invalid is invalid!" == e.value.message


def test_validate_family_when_corpus_invalid(corpus_repo_mock):
    corpus_repo_mock.valid = False

    test_family = {
        "import_id": "test.new.family.0",
    }

    with pytest.raises(ValidationError) as e:
        validation_service.validate_family(test_family, "invalid")
    assert "Corpus 'invalid' not found" == e.value.message


def test_validate_family_when_category_invalid(corpus_repo_mock, geography_repo_mock):
    test_family = {
        "import_id": "test.new.family.0",
        "category": "Test",
    }

    with pytest.raises(ValidationError) as e:
        validation_service.validate_family(test_family, "test")
    assert "Test is not a valid FamilyCategory" == e.value.message


def test_validate_family_when_collection_ids_invalid(
    corpus_repo_mock, geography_repo_mock
):
    test_family = {
        "import_id": "test.new.family.0",
        "category": "UNFCCC",
        "collections": ["invalid"],
    }

    with pytest.raises(ValidationError) as e:
        validation_service.validate_family(test_family, "test")
    assert "The import ids are invalid: ['invalid']" == e.value.message


def test_validate_family_when_metadata_not_found(
    corpus_repo_mock, geography_repo_mock, collection_repo_mock, db_client_metadata_mock
):
    db_client_metadata_mock.bad_taxonomy = True

    test_family = {
        "import_id": "test.new.family.0",
        "category": "UNFCCC",
        "collections": [],
        "metadata": {},
    }

    with pytest.raises(ValidationError) as e:
        validation_service.validate_family(test_family, "test")
    assert "No taxonomy found for corpus" == e.value.message


def test_validate_family_when_metadata_invalid(
    corpus_repo_mock, geography_repo_mock, collection_repo_mock, db_client_metadata_mock
):
    test_family = {
        "import_id": "test.new.family.0",
        "category": "UNFCCC",
        "metadata": {},
        "collections": [],
    }

    with pytest.raises(ValidationError) as e:
        validation_service.validate_family(test_family, "test")
    assert "Metadata validation failed: Missing metadata keys:" in e.value.message
