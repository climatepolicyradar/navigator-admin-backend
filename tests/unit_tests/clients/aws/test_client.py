import json

import pytest
from botocore.exceptions import ClientError

from app.clients.aws.s3bucket import S3UploadConfig, upload_json_to_s3


def test_upload_json_to_s3_when_ok(basic_s3_client):
    basic_s3_client.create_bucket(
        Bucket="my-bucket",
        CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
    )
    config = S3UploadConfig(bucket_name="my-bucket", object_name="data.json")
    json_data = {"key": "value"}

    upload_json_to_s3(config, json_data)

    response = basic_s3_client.get_object(Bucket="my-bucket", Key="data.json")
    body = response["Body"].read().decode("utf-8")
    assert json.loads(body) == json_data


def test_upload_json_to_s3_when_error(basic_s3_client):
    config = S3UploadConfig(bucket_name="non-existent-bucket", object_name="data.json")
    json_data = {"key": "value"}

    with pytest.raises(ClientError) as e:
        upload_json_to_s3(config, json_data)

    assert e.value.response["Error"]["Code"] == "NoSuchBucket"
