import json
import logging
import os
from unittest.mock import Mock, patch

import pytest

import app.service.bulk_import as bulk_import_service
from app.errors import ValidationError


@patch("app.service.bulk_import.uuid4", Mock(return_value="1111-1111"))
@patch.dict(os.environ, {"BULK_IMPORT_BUCKET": "test_bucket"})
@patch("app.service.bulk_import._exists_in_db", Mock(return_value=False))
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


@patch("app.service.bulk_import._exists_in_db", Mock(return_value=False))
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


@patch("app.service.bulk_import._exists_in_db", Mock(return_value=False))
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
@patch("app.service.bulk_import._exists_in_db", Mock(return_value=False))
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
