import json
import logging
import os
from unittest.mock import Mock, patch

import pytest

import app.service.ingest as ingest_service
from app.errors import ValidationError


@pytest.mark.skip("This code tests S3 and needs reinstating when that work is done.")
@patch("app.service.ingest._exists_in_db", Mock(return_value=False))
@patch.dict(os.environ, {"BULK_IMPORT_BUCKET": "test_bucket"})
def test_ingest_when_ok(
    basic_s3_client,
    corpus_repo_mock,
    geography_repo_mock,
    collection_repo_mock,
    family_repo_mock,
    document_repo_mock,
    event_repo_mock,
    validation_service_mock,
):
    bucket_name = "test_bucket"
    test_data = {
        "collections": [
            {
                "import_id": "test.new.collection.0",
                "title": "Test title",
                "description": "Test description",
            },
        ],
        "families": [
            {
                "import_id": "test.new.family.0",
                "title": "Test",
                "summary": "Test",
                "geographies": ["Test"],
                "category": "UNFCCC",
                "metadata": {"color": ["blue"], "size": [""]},
                "collections": ["test.new.collection.0"],
            },
        ],
        "documents": [
            {
                "import_id": "test.new.document.0",
                "family_import_id": "test.new.family.0",
                "variant_name": "Original Language",
                "metadata": {"color": ["blue"]},
                "title": "",
                "source_url": None,
                "user_language_name": "",
            }
        ],
        "events": [
            {
                "import_id": "test.new.event.0",
                "family_import_id": "test.new.family.0",
                "event_title": "Test",
                "date": "2000-01-01T00:00:00.000Z",
                "event_type_value": "Amended",
            }
        ],
    }

    expected_ingest_result = {
        "collections": ["test.new.collection.0"],
        "families": ["test.new.family.0"],
        "documents": ["test.new.document.0"],
        "events": ["test.new.event.0"],
    }

    try:
        with (
            patch(
                "app.service.ingest.notification_service.send_notification"
            ) as mock_notification_service,
        ):
            ingest_service.import_data(test_data, "test_corpus_id")

            response = basic_s3_client.list_objects_v2(
                Bucket=bucket_name, Prefix="1111-1111-result-test_corpus_id"
            )

            assert 2 == mock_notification_service.call_count
            mock_notification_service.assert_called_with(
                "🎉 Bulk import for corpus: test_corpus_id successfully completed."
            )

            objects = response["Contents"]
            assert len(objects) == 1

            key = objects[0]["Key"]
            response = basic_s3_client.get_object(Bucket=bucket_name, Key=key)
            body = response["Body"].read().decode("utf-8")
            assert expected_ingest_result == json.loads(body)
    except Exception as e:
        assert False, f"import_data in ingest service raised an exception: {e}"


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
        ingest_service.import_data(test_data, "test")

    assert "The import id invalid is invalid!" in caplog.text


@patch("app.service.ingest._exists_in_db", Mock(return_value=False))
@patch.dict(os.environ, {"BULK_IMPORT_BUCKET": "test_bucket"})
def test_ingest_when_db_error(
    caplog, basic_s3_client, corpus_repo_mock, collection_repo_mock
):
    collection_repo_mock.throw_repository_error = True

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
            "app.service.ingest.notification_service.send_notification"
        ) as mock_notification_service,
    ):
        ingest_service.import_data(test_data, "test")

    assert 2 == mock_notification_service.call_count
    mock_notification_service.assert_called_with(
        "💥 Bulk import for corpus: test has failed."
    )
    assert (
        "Rolling back transaction due to the following error: bad collection repo"
        in caplog.text
    )


@pytest.mark.skip("This code tests S3 and needs reinstating when that work is done.")
@patch.dict(os.environ, {"BULK_IMPORT_BUCKET": "test_bucket"})
def test_request_json_saved_to_s3_on_ingest(basic_s3_client):
    bucket_name = "test_bucket"
    json_data = {"key": "value"}

    ingest_service.import_data({"key": "value"}, "test_corpus_id")

    response = basic_s3_client.list_objects_v2(
        Bucket=bucket_name, Prefix="1111-1111-request-test_corpus_id"
    )

    assert "Contents" in response
    objects = response["Contents"]
    assert len(objects) == 1

    key = objects[0]["Key"]
    response = basic_s3_client.get_object(Bucket=bucket_name, Key=key)
    body = response["Body"].read().decode("utf-8")
    assert json.loads(body) == json_data


def test_save_families_when_corpus_invalid(corpus_repo_mock, validation_service_mock):
    corpus_repo_mock.error = True

    test_data = [{"import_id": "test.new.family.0"}]

    with pytest.raises(ValidationError) as e:
        ingest_service.save_families(test_data, "test")
    assert "No organisation associated with corpus test" == e.value.message


def test_save_families_when_data_invalid(corpus_repo_mock, validation_service_mock):
    validation_service_mock.throw_validation_error = True
    test_data = [{"import_id": "invalid"}]

    with pytest.raises(ValidationError) as e:
        ingest_service.save_families(test_data, "test")
    assert "Error" == e.value.message


def test_save_documents_when_data_invalid(validation_service_mock):
    validation_service_mock.throw_validation_error = True

    test_data = [{"import_id": "invalid"}]

    with pytest.raises(ValidationError) as e:
        ingest_service.save_documents(test_data, "test")
    assert "Error" == e.value.message


@patch("app.service.ingest._exists_in_db", Mock(return_value=False))
def test_do_not_save_documents_over_ingest_limit(
    validation_service_mock, document_repo_mock, monkeypatch
):
    monkeypatch.setattr(ingest_service, "DOCUMENT_INGEST_LIMIT", 1)

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

    saved_documents = ingest_service.save_documents(test_data, "test")
    assert ["test.new.document.0"] == saved_documents


def test_save_events_when_data_invalid(validation_service_mock):
    validation_service_mock.throw_validation_error = True

    test_data = [{"import_id": "invalid"}]

    with pytest.raises(ValidationError) as e:
        ingest_service.save_events(test_data, "test")
    assert "Error" == e.value.message
