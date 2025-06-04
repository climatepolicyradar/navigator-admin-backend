import pytest

import app.service.validation as validation_service
from app.errors import ValidationError


def test_validate_event_when_ok(db_client_metadata_mock, db_session_mock):
    event_metadata = {"color": ["pink"]}
    test_event = {
        "import_id": "test.new.event.0",
        "family_import_id": "test.new.family.0",
        "event_type_value": event_metadata,
        "metadata": event_metadata,
    }

    validation_service.validate_event(db_session_mock, test_event, "test")


def test_validate_new_event_schema_when_ok(db_client_metadata_mock, db_session_mock):
    test_event = {
        "import_id": "test.new.event.0",
        "family_import_id": "test.new.family.0",
        "family_document_import_id": "test.new.document.0",
        "event_type_value": "published",
        "metadata": {"color": ["pink"]},
    }

    validation_service.validate_event(db_session_mock, test_event, "test")


def test_validate_event_when_import_id_wrong_format(db_session_mock):
    invalid_import_id = "invalid"
    test_event = {
        "import_id": invalid_import_id,
    }

    with pytest.raises(ValidationError) as e:
        validation_service.validate_event(db_session_mock, test_event, "test")
    assert f"The import id {invalid_import_id} is invalid!" == e.value.message


def test_validate_event_when_family_import_id_wrong_format(db_session_mock):
    invalid_import_id = "invalid"
    test_event = {
        "import_id": "test.new.event.0",
        "family_import_id": invalid_import_id,
    }

    with pytest.raises(ValidationError) as e:
        validation_service.validate_event(db_session_mock, test_event, "test")
    assert f"The import id {invalid_import_id} is invalid!" == e.value.message


def test_validate_event_when_event_metadata_has_invalid_type(
    db_client_metadata_mock, db_session_mock
):
    invalid_event_type = "invalid"
    event_metadata = {"color": invalid_event_type}
    test_event = {
        "import_id": "test.new.event.0",
        "family_import_id": "test.new.family.0",
        "event_type_value": event_metadata,
        "metadata": event_metadata,
    }

    with (pytest.raises(ValidationError) as e,):
        validation_service.validate_event(db_session_mock, test_event, "test")
    assert (
        f"Metadata validation failed: Invalid value '{invalid_event_type}' "
        "for metadata key 'color' expected list." == e.value.message
    )


def test_validate_event_when_event_not_in_allowed_event_types(
    db_client_metadata_mock, db_session_mock
):
    invalid_event_type = ["invalid"]
    event_metadata = {"color": invalid_event_type}
    test_event = {
        "import_id": "test.new.event.0",
        "family_import_id": "test.new.family.0",
        "event_type_value": event_metadata,
        "metadata": event_metadata,
    }

    with pytest.raises(ValidationError) as e:
        validation_service.validate_event(db_session_mock, test_event, "test")
    assert (
        f"Metadata validation failed: Invalid value '{invalid_event_type}' "
        "for metadata key 'color'" == e.value.message
    )
