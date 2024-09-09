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
    expected_msg = "The import id invalid is invalid!"
    assert e.value.message == expected_msg
