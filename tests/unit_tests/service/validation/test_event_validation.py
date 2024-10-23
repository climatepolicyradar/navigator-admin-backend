import pytest

import app.service.validation as validation_service
from app.errors import ValidationError


def test_validate_event_when_ok(db_client_metadata_mock):
    test_event = {
        "import_id": "test.new.event.0",
        "family_import_id": "test.new.family.0",
        "event_type_value": {"color": ["pink"]},
    }

    validation_service.validate_event(test_event, "test")


def test_validate_event_when_import_id_wrong_format():
    invalid_import_id = "invalid"
    test_event = {
        "import_id": invalid_import_id,
    }

    with pytest.raises(ValidationError) as e:
        validation_service.validate_event(test_event, "test")
    assert f"The import id {invalid_import_id} is invalid!" == e.value.message


def test_validate_event_when_family_import_id_wrong_format():
    invalid_import_id = "invalid"
    test_event = {
        "import_id": "test.new.event.0",
        "family_import_id": invalid_import_id,
    }

    with pytest.raises(ValidationError) as e:
        validation_service.validate_event(test_event, "test")
    assert f"The import id {invalid_import_id} is invalid!" == e.value.message


def test_validate_event_when_event_metadata_has_invalid_type(db_client_metadata_mock):
    invalid_event_type = "invalid"
    test_event = {
        "import_id": "test.new.event.0",
        "family_import_id": "test.new.family.0",
        "event_type_value": {"color": invalid_event_type},
    }

    with pytest.raises(ValidationError) as e:
        validation_service.validate_event(test_event, "test")
    assert (
        f"Metadata validation failed: Invalid value '{invalid_event_type}' "
        "for metadata key 'color' expected list." == e.value.message
    )


def test_validate_event_when_event_not_in_allowed_event_types(db_client_metadata_mock):
    invalid_event_type = ["invalid"]
    test_event = {
        "import_id": "test.new.event.0",
        "family_import_id": "test.new.family.0",
        "event_type_value": {"color": invalid_event_type},
    }

    with pytest.raises(ValidationError) as e:
        validation_service.validate_event(test_event, "test")
    assert (
        f"Metadata validation failed: Invalid value '{invalid_event_type}' "
        "for metadata key 'color'" == e.value.message
    )
