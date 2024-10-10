import json
import os
from unittest.mock import patch

import pytest
from botocore.exceptions import ClientError

from app.clients.aws.s3bucket import (
    S3UploadContext,
    upload_ingest_json_to_s3,
    upload_json_to_s3,
)
from tests.helpers.utils import cleanup_local_files


def test_upload_json_to_s3_when_ok(basic_s3_client):
    basic_s3_client.create_bucket(
        Bucket="my-bucket",
        CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
    )
    context = S3UploadContext(bucket_name="my-bucket", object_name="data.json")
    json_data = {"key": "value"}

    upload_json_to_s3(basic_s3_client, context, json_data)

    response = basic_s3_client.get_object(Bucket="my-bucket", Key="data.json")
    body = response["Body"].read().decode("utf-8")
    assert json.loads(body) == json_data


def test_upload_json_to_s3_when_error(basic_s3_client):
    context = S3UploadContext(
        bucket_name="non-existent-bucket", object_name="data.json"
    )
    json_data = {"key": "value"}

    with pytest.raises(ClientError) as e:
        upload_json_to_s3(basic_s3_client, context, json_data)

    assert e.value.response["Error"]["Code"] == "NoSuchBucket"


@patch.dict(os.environ, {"BULK_IMPORT_BUCKET": "test_bucket"})
def test_upload_ingest_json_to_s3_success(basic_s3_client):
    print(">>>>>>>>>>>>>>>>>>>", os.getenv("BULK_IMPORT_BUCKET", "Nothing"))
    json_data = {"test": "test"}
    upload_ingest_json_to_s3("1111-1111", "test_corpus_id", json_data)

    find_response = basic_s3_client.list_objects_v2(
        Bucket="test_bucket", Prefix="1111-1111-test_corpus_id"
    )

    assert len(find_response["Contents"]) == 1

    saved_file_name = find_response["Contents"][0]["Key"]
    get_response = basic_s3_client.get_object(Bucket="test_bucket", Key=saved_file_name)
    body = get_response["Body"].read().decode("utf-8")

    assert json.loads(body) == json_data


@patch.dict(os.environ, {"BULK_IMPORT_BUCKET": "skip"})
def test_do_not_save_ingest_json_to_s3_when_in_local_development(basic_s3_client):
    json_data = {"test": "test"}

    upload_ingest_json_to_s3("1111-1111", "test_corpus_id", json_data)

    find_response = basic_s3_client.list_objects_v2(
        Bucket="test_bucket", Prefix="1111-1111-test_corpus_id"
    )

    assert "Contents" not in find_response
    cleanup_local_files("bulk_import_results/1111-1111-test_corpus_id*")
