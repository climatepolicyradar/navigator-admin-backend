"""Integration tests for corpus logo upload functionality."""

import os
from typing import cast
from unittest.mock import patch

import boto3
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from moto import mock_aws
from sqlalchemy.orm import Session

from tests.integration_tests.setup_db import setup_db


@pytest.fixture
def s3_bucket_name():
    """Fixture for S3 bucket name."""
    return "test-corpus-logos"


@pytest.fixture
def s3_client(s3_bucket_name):
    """Fixture for mocked S3 client."""
    with mock_aws():
        with patch.dict(
            os.environ,
            {
                "AWS_ACCESS_KEY_ID": "test",
                "AWS_SECRET_ACCESS_KEY": "test",
                "AWS_ENDPOINT_URL": "",
                "S3_CORPUS_LOGO_BUCKET": s3_bucket_name,
                "CDN_URL": "https://cdn.test.com",
                "CACHE_BUCKET": "some-cache-bucket",
            },
        ):
            s3 = boto3.client("s3")
            s3.create_bucket(
                Bucket=s3_bucket_name,
                CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
            )
            yield s3


def test_upload_flow(
    client: TestClient,
    data_db: Session,
    s3_client,
    s3_bucket_name,
    superuser_header_token,
):
    """Test the complete flow of getting a URL and uploading a file."""
    setup_db(data_db)

    # Get the upload URL
    response = client.post(
        "/api/v1/corpora/CCLW.corpus.i00000001.n0000/upload-url",
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    print(data["presigned_upload_url"])
    print(data["object_cdn_url"])

    # Verify the URLs are correctly formatted
    assert cast(str, data["presigned_upload_url"]).startswith("https://")
    assert cast(str, data["object_cdn_url"]).startswith("https://cdn.test.com")

    # Extract the S3 key from the CDN URL
    cdn_path = cast(str, data["object_cdn_url"]).replace("https://cdn.test.com/", "")

    # Simulate uploading a file using the presigned URL
    test_content = b"test image content"
    s3_client.put_object(
        Bucket=s3_bucket_name, Key=cdn_path, Body=test_content, ContentType="image/png"
    )

    # Verify the file was uploaded
    response = s3_client.get_object(Bucket=s3_bucket_name, Key=cdn_path)
    assert response["Body"].read() == test_content
    assert response["ContentType"] == "image/png"


def test_upload_url_invalid_corpus(
    client: TestClient, data_db: Session, s3_client, superuser_header_token
):
    """Test getting upload URL for non-existent corpus."""
    setup_db(data_db)

    response = client.post(
        "/api/v1/corpora/NONEXISTENT.corpus.id/upload-url",
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "detail" in data
    assert "'NONEXISTENT.corpus.id' not found" in data["detail"]
