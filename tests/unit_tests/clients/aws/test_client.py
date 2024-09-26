import json

import boto3
import pytest
from moto import mock_s3

from app.clients.aws.client import S3UploadConfig, upload_json_to_s3


@pytest.fixture
def aws_credentials(monkeypatch):
    """Mocked AWS Credentials for moto."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")


@pytest.fixture
def s3_client(aws_credentials):
    with mock_s3():
        conn = boto3.client("s3", region_name="eu-west-2")
        yield conn


def test_upload_json_to_s3(s3_client):
    s3_client.create_bucket(
        Bucket="my-bucket",
        CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
    )
    config = S3UploadConfig(bucket_name="my-bucket", object_name="data.json")
    json_data = {"key": "value"}

    upload_json_to_s3(config, json_data)

    response = s3_client.get_object(Bucket="my-bucket", Key="data.json")
    body = response["Body"].read().decode("utf-8")
    assert json.loads(body) == json_data
