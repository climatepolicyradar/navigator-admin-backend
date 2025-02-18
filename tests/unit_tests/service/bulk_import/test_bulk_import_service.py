import json
import logging
import os
from unittest.mock import Mock, create_autospec, patch

import pytest
from db_client.models.dfce.collection import Collection
from db_client.models.dfce.family import Family
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Session
from tests.helpers.bulk_import import default_document, default_family

import app.service.bulk_import as bulk_import_service
from app.errors import ValidationError


@patch("app.service.bulk_import.uuid4", Mock(return_value="1111-1111"))
@patch.dict(os.environ, {"BULK_IMPORT_BUCKET": "test_bucket"})
@patch("app.service.bulk_import._find_entity_in_db", Mock(return_value=False))
def test_input_json_and_result_saved_to_s3_on_bulk_import(
    basic_s3_client, validation_service_mock, corpus_repo_mock, collection_repo_mock
):
    bucket_name = "test_bucket"
    json_data = {
        "collections": [
            {
                "import_id": "test.new.collection.0",
                "title": "Test title",
                "description": "Test description",
            }
        ]
    }

    bulk_import_service.import_data(json_data, "test_corpus_id")

    bulk_import_input_json = basic_s3_client.list_objects_v2(
        Bucket=bucket_name, Prefix="1111-1111-result-test_corpus_id"
    )
    objects = bulk_import_input_json["Contents"]
    assert len(objects) == 1

    key = objects[0]["Key"]
    bulk_import_result = basic_s3_client.get_object(Bucket=bucket_name, Key=key)
    body = bulk_import_result["Body"].read().decode("utf-8")
    assert {"collections": ["test.new.collection.0"]} == json.loads(body)


@patch("app.service.bulk_import._find_entity_in_db", Mock(return_value=False))
@patch.dict(os.environ, {"BULK_IMPORT_BUCKET": "test_bucket"})
def test_slack_notification_sent_on_success(
    basic_s3_client,
    corpus_repo_mock,
    collection_repo_mock,
    validation_service_mock,
):
    test_data = {
        "collections": [
            {
                "import_id": "test.new.collection.0",
                "title": "Test title",
                "description": "Test description",
            }
        ],
    }

    with (
        patch(
            "app.service.bulk_import.notification_service.send_notification"
        ) as mock_notification_service,
    ):
        bulk_import_service.import_data(test_data, "test_corpus_id")

        assert 2 == mock_notification_service.call_count
        mock_notification_service.assert_called_with(
            "🎉 Bulk import for corpus: test_corpus_id successfully completed."
        )


@patch("app.service.bulk_import._find_entity_in_db", Mock(return_value=False))
@patch.dict(os.environ, {"BULK_IMPORT_BUCKET": "test_bucket"})
def test_slack_notification_sent_on_error(caplog, basic_s3_client, corpus_repo_mock):
    corpus_repo_mock.error = True

    test_data = {
        "collections": [
            {
                "import_id": "test.new.collection.0",
                "title": "Test title",
                "description": "Test description",
            }
        ]
    }

    with (
        caplog.at_level(logging.ERROR),
        patch(
            "app.service.bulk_import.notification_service.send_notification"
        ) as mock_notification_service,
    ):
        bulk_import_service.import_data(test_data, "test")

    assert 2 == mock_notification_service.call_count
    mock_notification_service.assert_called_with(
        "💥 Bulk import for corpus: test has failed."
    )
    assert (
        "Rolling back transaction due to the following error: No organisation associated with corpus test"
        in caplog.text
    )


@pytest.mark.parametrize(
    "test_data",
    [
        {"families": [{**default_family, "metadata": {"key": [1]}}]},
        {"families": [{**default_family, "metadata": {"key": None}}]},
        {"families": [{**default_family, "metadata": {"key": 1}}]},
        {"documents": [{**default_document, "metadata": {"key": 1}}]},
    ],
)
@patch.dict(os.environ, {"BULK_IMPORT_BUCKET": "test_bucket"})
@patch("app.service.bulk_import._find_entity_in_db", Mock(return_value=False))
def test_import_data_when_metadata_contains_non_string_values(
    test_data,
    corpus_repo_mock,
    validation_service_mock,
    caplog,
    basic_s3_client,
):
    with caplog.at_level(logging.ERROR):
        bulk_import_service.import_data(test_data, "test")

    assert "Input should be a valid string" in caplog.text


@patch.dict(os.environ, {"BULK_IMPORT_BUCKET": "test_bucket"})
def test_import_data_when_data_invalid(caplog, basic_s3_client):
    test_data = {
        "collections": [
            {
                "import_id": "invalid",
                "title": "Test title",
                "description": "Test description",
            }
        ]
    }

    with caplog.at_level(logging.ERROR):
        bulk_import_service.import_data(test_data, "test")

    assert "The import id invalid is invalid!" in caplog.text


def test_save_families_when_corpus_invalid(corpus_repo_mock, validation_service_mock):
    corpus_repo_mock.error = True

    test_data = [{"import_id": "test.new.family.0"}]

    with pytest.raises(ValidationError) as e:
        bulk_import_service.save_families(test_data, "test")
    assert "No organisation associated with corpus test" == e.value.message


def test_save_families_when_data_invalid(corpus_repo_mock, validation_service_mock):
    validation_service_mock.throw_validation_error = True
    test_data = [{"import_id": "invalid"}]

    with pytest.raises(ValidationError) as e:
        bulk_import_service.save_families(test_data, "test")
    assert "Error" == e.value.message


def test_save_documents_when_data_invalid(validation_service_mock):
    validation_service_mock.throw_validation_error = True

    test_data = [{"import_id": "invalid"}]

    with pytest.raises(ValidationError) as e:
        bulk_import_service.save_documents(test_data, "test", 1)
    assert "Error" == e.value.message


@patch("app.service.bulk_import.generate_slug", Mock(return_value="test-slug_1234"))
@patch("app.service.bulk_import._find_entity_in_db", Mock(return_value=False))
def test_do_not_save_documents_over_bulk_import_limit(
    validation_service_mock, document_repo_mock, monkeypatch
):
    test_data = [
        {
            "import_id": "test.new.document.0",
            "family_import_id": "test.new.family.0",
            "variant_name": "Original Language",
            "metadata": {"color": ["blue"]},
            "title": "",
            "source_url": None,
            "user_language_name": "",
        },
        {
            "import_id": "test.new.document.1",
            "family_import_id": "test.new.family.1",
            "variant_name": "Original Language",
            "metadata": {"color": ["blue"]},
            "title": "",
            "source_url": None,
            "user_language_name": "",
        },
    ]

    saved_documents = bulk_import_service.save_documents(test_data, "test", 1)
    assert ["test.new.document.0"] == saved_documents


def test_save_events_when_data_invalid(validation_service_mock):
    validation_service_mock.throw_validation_error = True

    test_data = [{"import_id": "invalid"}]

    with pytest.raises(ValidationError) as e:
        bulk_import_service.save_events(test_data, "test")
    assert "Error" == e.value.message


def test_save_collections_skips_update_when_no_changes(
    collection_repo_mock,
    corpus_repo_mock,
    validation_service_mock,
):

    test_data = [
        {
            "import_id": "test.new.collection.0",
            "title": "Test title",
            "description": "Test description",
        }
    ]
    mock_collection = Mock(spec=Collection)
    mock_collection.import_id = test_data[0]["import_id"]
    mock_collection.title = test_data[0]["title"]
    mock_collection.description = test_data[0]["description"]
    mock_collection.created = ""
    mock_collection.last_modified = ""

    with patch(
        "app.service.bulk_import._find_entity_in_db", return_value=mock_collection
    ):
        result = bulk_import_service.save_collections(test_data, "test_corpus_id")

    assert collection_repo_mock.update.call_count == 0
    assert result == []


def test_save_families_skips_update_when_no_changes(
    family_repo_mock,
    corpus_repo_mock,
    geography_repo_mock,
    validation_service_mock,
):
    test_metadata = {"metadata_key": ["metadata_value"]}
    test_data = [
        {
            "import_id": "test.new.collection.0",
            "title": "Test title",
            "summary": "Test description",
            "geographies": ["XAA"],
            "category": "Executive",
            "metadata": test_metadata,
            "collections": [],
        }
    ]

    class MockFamily(Family):
        @hybrid_property
        def last_updated_date(self):
            return None

        @hybrid_property
        def published_date(self):
            return None

    mock_family = Mock(spec=MockFamily)
    mock_family.import_id = test_data[0]["import_id"]
    mock_family.title = test_data[0]["title"]
    mock_family.description = test_data[0]["summary"]
    mock_family.geographies = [Mock(value=geo) for geo in test_data[0]["geographies"]]
    mock_family.family_category = test_data[0]["category"]
    mock_family.family_documents = []
    mock_family.slugs = []
    mock_family.events = None
    mock_family.created = ""
    mock_family.last_modified = ""

    mock_db = create_autospec(Session)
    mock_db.query.return_value.filter.return_value.one_or_none.return_value = Mock(
        value=test_metadata
    )

    with patch("app.service.bulk_import._find_entity_in_db", return_value=mock_family):
        result = bulk_import_service.save_families(
            test_data, "test_corpus_id", db=mock_db
        )

    assert family_repo_mock.update.call_count == 0
    assert result == []
