import pytest

import app.service.ingest as ingest_service
from app.errors import ValidationError


def test_ingest_collections_when_import_id_wrong_format(corpus_service_mock):

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


def test_ingest_families_when_geography_invalid(
    corpus_service_mock, geography_repo_mock
):
    geography_repo_mock.error = True
    test_data = {
        "families": [
            {
                "import_id": "test.new.family.0",
                "title": "Test",
                "summary": "Test",
                "geography": "invalid",
                "category": "UNFCCC",
                "metadata": {},
                "collections": [],
                "events": [],
                "documents": [],
            },
        ],
    }
    with pytest.raises(ValidationError) as e:
        ingest_service.import_data(test_data, "test")
    expected_msg = "The geography value invalid is invalid!"
    assert e.value.message == expected_msg
