import pytest

import app.service.validation as validation_service
from app.errors import ValidationError


def test_validate_event_when_ok():
    test_event = {
        "import_id": "test.new.event.0",
        "family_import_id": "test.new.family.0",
        "event_type_value": "Amended",
    }

    validation_service.validate_event(
        test_event, {"event_type": {"allowed_values": ["Amended"]}}
    )


def test_validate_event_when_import_id_wrong_format():
    invalid_import_id = "invalid"
    test_event = {
        "import_id": invalid_import_id,
    }

    with pytest.raises(ValidationError) as e:
        validation_service.validate_event(test_event, {})
    assert f"The import id {invalid_import_id} is invalid!" == e.value.message


def test_validate_event_when_family_import_id_wrong_format():
    invalid_import_id = "invalid"
    test_event = {
        "import_id": "test.new.event.0",
        "family_import_id": invalid_import_id,
    }

    with pytest.raises(ValidationError) as e:
        validation_service.validate_event(test_event, {})
    assert f"The import id {invalid_import_id} is invalid!" == e.value.message


def test_validate_event_when_event_type_invalid():
    invalid_event_type = "invalid"
    test_event = {
        "import_id": "test.new.event.0",
        "family_import_id": "test.new.family.0",
        "event_type_value": invalid_event_type,
    }

    with pytest.raises(ValidationError) as e:
        validation_service.validate_event(
            test_event, {"event_type": {"allowed_values": ["test"]}}
        )
    assert f"Event type ['{invalid_event_type}'] is invalid!" == e.value.message
