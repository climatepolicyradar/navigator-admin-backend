import json
import logging
import os
from unittest.mock import Mock, patch

import pytest

import app.service.bulk_import as bulk_import_service
from app.errors import ValidationError
from tests.helpers.bulk_import import default_document, default_family


@patch("app.service.bulk_import.uuid4", Mock(return_value="1111-1111"))
@patch.dict(os.environ, {"BULK_IMPORT_BUCKET": "test_bucket"})
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
def test_import_data_when_metadata_contains_non_string_values(
    test_data,
    family_repo_mock,
    document_repo_mock,
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
def test_do_not_save_documents_over_bulk_import_limit(
    validation_service_mock, document_repo_mock, monkeypatch
):
    document_repo_mock.return_empty = True
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
    collection_repo_mock, corpus_repo_mock, validation_service_mock
):
    collection_repo_mock.return_empty = True
    test_data = [
        {
            "import_id": "test.new.collection.0",
            "title": "title",
            "description": "description",
        }
    ]

    result = bulk_import_service.save_collections(test_data, "test_corpus_id")

    assert collection_repo_mock.update.call_count == 0
    assert result == []


def test_save_families_skips_update_when_no_changes(
    family_repo_mock, corpus_repo_mock, geography_repo_mock, validation_service_mock
):
    test_data = [
        {
            "import_id": "test.new.family.0",
            "title": "title",
            "summary": "summary",
            "geographies": ["BRB", "CHN", "BHS"],
            "category": "Legislative",
            "metadata": {
                "topic": [],
                "hazard": [],
                "sector": [],
                "keyword": [],
                "framework": [],
                "instrument": [],
            },
            "collections": ["x.y.z.1", "x.y.z.2"],
        }
    ]

    result = bulk_import_service.save_families(test_data, "CCLW.corpus.i00000001.n0000")

    assert family_repo_mock.update.call_count == 0
    assert result == []


def test_save_documents_skips_update_when_no_changes(
    document_repo_mock, corpus_repo_mock, validation_service_mock
):

    test_data = [
        {
            "import_id": "test.new.document.0",
            "family_import_id": "test.family.1.0",
            "title": "title",
            "variant_name": "Original Language",
            "metadata": {"role": ["MAIN"], "type": ["Law"]},
            "source_url": "http://source",
            "user_language_name": "Ghotuo",
        }
    ]

    result = bulk_import_service.save_documents(
        test_data, "test_corpus_id", document_limit=1
    )

    assert document_repo_mock.update.call_count == 0
    assert result == []


@patch(
    "app.service.bulk_import.create_event_metadata_object",
    Mock(
        return_value={
            "event_type": ["Amended"],
            "datetime_event_name": ["Amended"],
        }
    ),
)
def test_save_events_skips_update_when_no_changes(
    event_repo_mock, corpus_repo_mock, validation_service_mock
):
    test_data = [
        {
            "import_id": "test.new.collection.0",
            "family_import_id": "test.family.1.0",
            "family_document_import_id": None,
            "event_title": "title",
            "date": "2020-01-01",
            "event_type_value": "Amended",
        }
    ]

    result = bulk_import_service.save_events(test_data, "test_corpus_id")

    assert event_repo_mock.update.call_count == 0
    assert result == []
