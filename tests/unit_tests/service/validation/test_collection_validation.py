import pytest

import app.service.validation as validation_service
from app.errors import ValidationError


def test_validate_collection_when_ok():
    test_collection = {
        "import_id": "test.new.collection.0",
    }

    validation_service.validate_collection(test_collection)


def test_validate_collection_when_import_id_invalid():
    invalid_import_id = "invalid"
    test_collection = {
        "import_id": invalid_import_id,
    }

    with pytest.raises(ValidationError) as e:
        validation_service.validate_collection(test_collection)
    assert "The import id invalid is invalid!" == e.value.message
