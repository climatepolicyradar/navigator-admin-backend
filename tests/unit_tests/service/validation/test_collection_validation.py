import pytest

import app.service.validation as validation_service
from app.errors import ValidationError


def test_validate_collection_when_ok():
    test_collection = {
        "import_id": "test.new.collection.0",
        "title": "Test title",
        "description": "Test description",
    }

    validation_service.validate_collection(test_collection)


def test_validate_collection_when_import_id_invalid():
    invalid_import_id = "invalid"
    test_collection = {
        "import_id": invalid_import_id,
        "title": "Test title",
        "description": "Test description",
    }

    with pytest.raises(ValidationError) as e:
        validation_service.validate_collection(test_collection)
    assert e.value.message == "The import id invalid is invalid!"


def test_validate_family_when_ok(corpus_repo_mock, db_client_metadata_mock):
    test_family = {
        "import_id": "test.new.family.0",
        "title": "Test",
        "summary": "Test",
        "geography": "Test",
        "category": "UNFCCC",
        "metadata": {"color": ["blue"], "size": [""]},
        "collections": ["test.new.collection.0"],
    }

    validation_service.validate_family(test_family, "test")


def test_validate_family_when_import_id_invalid(corpus_repo_mock):
    invalid_import_id = "invalid"
    test_family = {
        "import_id": invalid_import_id,
        "title": "Test",
        "summary": "Test",
        "geography": "Test",
        "category": "UNFCCC",
        "metadata": {"color": ["blue"], "size": [""]},
        "collections": ["test.new.collection.0"],
    }

    with pytest.raises(ValidationError) as e:
        validation_service.validate_family(test_family, "test")
    assert e.value.message == "The import id invalid is invalid!"


def test_validate_family_when_corpus_invalid(corpus_repo_mock):
    corpus_repo_mock.valid = False

    test_family = {
        "import_id": "test.new.family.0",
        "title": "Test",
        "summary": "Test",
        "geography": "Test",
        "category": "Test",
        "metadata": {},
        "collections": [],
    }

    with pytest.raises(ValidationError) as e:
        validation_service.validate_family(test_family, "invalid")
    assert e.value.message == "Corpus 'invalid' not found"


def test_validate_family_when_category_invalid(corpus_repo_mock, geography_repo_mock):
    test_family = {
        "import_id": "test.new.family.0",
        "title": "Test",
        "summary": "Test",
        "geography": "Invalid",
        "category": "Test",
        "metadata": {},
        "collections": [],
    }

    with pytest.raises(ValidationError) as e:
        validation_service.validate_family(test_family, "test")
    assert e.value.message == "Test is not a valid FamilyCategory"


def test_validate_family_when_collection_ids_invalid(
    corpus_repo_mock, geography_repo_mock
):
    test_family = {
        "import_id": "test.new.family.0",
        "title": "Test",
        "summary": "Test",
        "geography": "Test",
        "category": "UNFCCC",
        "metadata": {},
        "collections": ["invalid"],
    }

    with pytest.raises(ValidationError) as e:
        validation_service.validate_family(test_family, "test")
    assert e.value.message == "The import ids are invalid: ['invalid']"


def test_validate_family_when_metadata_not_found(
    corpus_repo_mock, geography_repo_mock, collection_repo_mock, db_client_metadata_mock
):
    db_client_metadata_mock.bad_taxonomy = True

    test_family = {
        "import_id": "test.new.family.0",
        "title": "Test",
        "summary": "Test",
        "geography": "Test",
        "category": "UNFCCC",
        "metadata": {},
        "collections": ["id.does.not.exist"],
    }

    with pytest.raises(ValidationError) as e:
        validation_service.validate_family(test_family, "test")
    assert e.value.message == "No taxonomy found for corpus"


def test_validate_family_when_metadata_invalid(
    corpus_repo_mock, geography_repo_mock, collection_repo_mock, db_client_metadata_mock
):
    test_family = {
        "import_id": "test.new.family.0",
        "title": "Test",
        "summary": "Test",
        "geography": "Test",
        "category": "UNFCCC",
        "metadata": {},
        "collections": ["id.does.not.exist"],
    }

    with pytest.raises(ValidationError) as e:
        validation_service.validate_family(test_family, "test")
    assert "Metadata validation failed: Missing metadata keys:" in e.value.message


def test_validate_document_when_ok(db_client_metadata_mock):
    test_document = {
        "import_id": "test.new.document.0",
        "family_import_id": "test.new.family.0",
        "variant_name": "Test",
        "metadata": {"color": ["blue"]},
        "events": [],
        "title": "",
        "user_language_name": "",
    }

    validation_service.validate_document(test_document, "test")


def test_validate_documents_when_import_id_wrong_format():
    invalid_import_id = "invalid"
    test_document = {
        "import_id": invalid_import_id,
        "family_import_id": "test.new.family.0",
        "variant_name": "Original Language",
        "metadata": {"color": ["blue"]},
        "events": [],
        "title": "",
        "source_url": None,
        "user_language_name": "",
    }

    with pytest.raises(ValidationError) as e:
        validation_service.validate_document(test_document, "test")
    assert e.value.message == f"The import id {invalid_import_id} is invalid!"


def test_validate_documents_when_family_import_id_wrong_format():
    invalid_family_import_id = "invalid"
    test_document = {
        "import_id": "test.new.document.0",
        "family_import_id": invalid_family_import_id,
        "variant_name": "Original Language",
        "metadata": {"color": ["blue"]},
        "events": [],
        "title": "",
        "source_url": None,
        "user_language_name": "",
    }

    with pytest.raises(ValidationError) as e:
        validation_service.validate_document(test_document, "test")
    assert e.value.message == f"The import id {invalid_family_import_id} is invalid!"


def test_validate_documents_when_variant_empty():
    test_document = {
        "import_id": "test.new.document.0",
        "family_import_id": "test.new.family.0",
        "variant_name": "",
        "metadata": {},
        "events": [],
        "title": "",
        "user_language_name": "",
    }

    with pytest.raises(ValidationError) as e:
        validation_service.validate_document(test_document, "test")
    assert e.value.message == "Variant name is empty"


def test_validate_documents_when_metadata_invalid(db_client_metadata_mock):
    test_document = {
        "import_id": "test.new.document.0",
        "family_import_id": "test.new.family.0",
        "variant_name": None,
        "metadata": {},
        "events": [],
        "title": "",
        "user_language_name": "",
    }

    with pytest.raises(ValidationError) as e:
        validation_service.validate_document(test_document, "test")
    assert "Metadata validation failed: Missing metadata keys:" in e.value.message
