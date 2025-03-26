import pytest

import app.service.validation as validation_service
from app.errors import ValidationError


def test_validate_document_when_ok(db_client_metadata_mock, db_session_mock):
    test_document = {
        "import_id": "test.new.document.0",
        "family_import_id": "test.new.family.0",
        "variant_name": "Test",
        "metadata": {"color": ["blue"]},
    }

    validation_service.validate_document(db_session_mock, test_document, "test")


def test_validate_document_when_import_id_wrong_format(db_session_mock):
    invalid_import_id = "invalid"
    test_document = {
        "import_id": invalid_import_id,
    }

    with pytest.raises(ValidationError) as e:
        validation_service.validate_document(db_session_mock, test_document, "test")
    assert f"The import id {invalid_import_id} is invalid!" == e.value.message


def test_validate_document_when_family_import_id_wrong_format(db_session_mock):
    invalid_family_import_id = "invalid"
    test_document = {
        "import_id": "test.new.document.0",
        "family_import_id": invalid_family_import_id,
    }

    with pytest.raises(ValidationError) as e:
        validation_service.validate_document(db_session_mock, test_document, "test")
    assert f"The import id {invalid_family_import_id} is invalid!" == e.value.message


def test_validate_document_when_variant_empty(db_session_mock):
    test_document = {
        "import_id": "test.new.document.0",
        "family_import_id": "test.new.family.0",
        "variant_name": "",
    }

    with pytest.raises(ValidationError) as e:
        validation_service.validate_document(db_session_mock, test_document, "test")
    assert "Variant name is empty" == e.value.message


def test_validate_document_when_metadata_invalid(
    db_client_metadata_mock, db_session_mock
):
    test_document = {
        "import_id": "test.new.document.0",
        "family_import_id": "test.new.family.0",
        "variant_name": None,
        "metadata": {},
    }

    with pytest.raises(ValidationError) as e:
        validation_service.validate_document(db_session_mock, test_document, "test")
    assert "Metadata validation failed: Missing metadata keys:" in e.value.message
