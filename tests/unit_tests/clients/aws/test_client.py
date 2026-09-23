import io
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest
import requests
from botocore.exceptions import ClientError

from app.clients.aws.client import get_s3_client
from app.clients.aws.s3bucket import (
    S3UploadContext,
    generate_pre_signed_url,
    get_upload_details,
    upload_bulk_import_json_to_s3,
    upload_csv_to_s3,
    upload_json_to_s3,
    upload_sql_db_dump_to_s3,
)


def test_generate_pre_signed_url_signs_in_cache_control_header(basic_s3_client):
    """A presigned URL generated with a cache_control value must sign
    Cache-Control into the SigV4 signed headers, so that only a PUT sending
    the matching header is accepted by S3 (verified directly against
    botocore's signer, since moto does not enforce SigV4 header validation
    the way real S3 does).

    Uses get_s3_client() (rather than the basic_s3_client fixture's plain
    boto3.client('s3')) because production explicitly configures SigV4 -
    the default client signature version doesn't reflect what generates the
    real presigned URLs.
    """
    with patch.dict(
        os.environ, {"AWS_ACCESS_KEY_ID": "test", "AWS_SECRET_ACCESS_KEY": "test"}
    ):
        client = get_s3_client()

    url = generate_pre_signed_url(
        client, "test_bucket", "logo.png", cache_control="no-cache"
    )

    query_params = parse_qs(urlparse(str(url)).query)
    signed_headers = query_params["X-Amz-SignedHeaders"][0]
    assert "cache-control" in signed_headers.split(";")

    matching_response = requests.put(
        str(url),
        data=b"image bytes",
        headers={"Cache-Control": "no-cache"},
    )
    assert matching_response.status_code == 200


def test_get_upload_details_forwards_cache_control(basic_s3_client):
    """get_upload_details must pass cache_control through to the presigned
    URL it generates, so callers can require a specific Cache-Control on
    upload without duplicating that plumbing themselves."""
    with patch.dict(
        os.environ, {"AWS_ACCESS_KEY_ID": "test", "AWS_SECRET_ACCESS_KEY": "test"}
    ):
        client = get_s3_client()

    presigned_url, _ = get_upload_details(
        client,
        "logo.png",
        "test_bucket",
        "https://cdn.test.com",  # type: ignore[arg-type]
        cache_control="no-cache",
    )

    query_params = parse_qs(urlparse(str(presigned_url)).query)
    signed_headers = query_params["X-Amz-SignedHeaders"][0]
    assert "cache-control" in signed_headers.split(";")


def test_get_s3_client_uses_default_credential_chain_when_env_vars_unset():
    """When AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY are not set (e.g. in ECS,
    where credentials should come from the task role), get_s3_client() must
    not pass explicit empty-string credentials to boto3 - doing so builds a
    static, resolved (but invalid) credentials object and prevents boto3
    from ever consulting its default credential chain (env vars, ECS task
    role, IMDS)."""
    with patch.dict(os.environ, {}, clear=True):
        client = get_s3_client()

    assert client._request_signer._credentials is None


def test_get_s3_client_uses_explicit_credentials_when_env_vars_set():
    with patch.dict(
        os.environ,
        {"AWS_ACCESS_KEY_ID": "test-key", "AWS_SECRET_ACCESS_KEY": "test-secret"},
    ):
        client = get_s3_client()

    credentials = client._request_signer._credentials
    assert credentials is not None
    assert credentials.access_key == "test-key"
    assert credentials.secret_key == "test-secret"


def test_upload_json_to_s3_when_ok(basic_s3_client):
    basic_s3_client.create_bucket(
        Bucket="my-bucket",
        CreateBucketConfiguration={"LocationConstraint": "eu-west-1"},
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
def test_upload_bulk_import_json_to_s3_success(basic_s3_client):
    json_data = {"test": "test"}
    upload_bulk_import_json_to_s3("1111-1111", "test_corpus_id", json_data)

    find_response = basic_s3_client.list_objects_v2(
        Bucket="test_bucket", Prefix="1111-1111-test_corpus_id"
    )

    assert len(find_response["Contents"]) == 1

    saved_file_name = find_response["Contents"][0]["Key"]
    get_response = basic_s3_client.get_object(Bucket="test_bucket", Key=saved_file_name)
    body = get_response["Body"].read().decode("utf-8")

    assert json.loads(body) == json_data


def test_upload_sql_db_dump_to_s3_raises_error_for_missing_bucket():
    with patch.dict(os.environ, {"DATABASE_DUMP_BUCKET": ""}):
        with pytest.raises(
            ValueError, match="DATABASE_DUMP_BUCKET environment variable not set"
        ):
            upload_sql_db_dump_to_s3("any_file.sql")


def test_upload_sql_db_dump_to_s3_raises_file_not_found_error():
    with patch.dict(os.environ, {"DATABASE_DUMP_BUCKET": "test_bucket"}):
        with pytest.raises(FileNotFoundError):
            upload_sql_db_dump_to_s3("nonexistent_file.sql")


@patch.dict(os.environ, {"DATABASE_DUMP_BUCKET": "test_bucket"})
def test_upload_sql_db_dump_to_s3_success(basic_s3_client):
    # Create realistic SQL dump content
    sql_dump_content = """-- MySQL dump 10.13  Distrib 8.0.33, for Linux (x86_64)
--
-- Host: localhost    Database: test_db
-- ------------------------------------------------------
-- Server version\t8.0.33-0ubuntu0.22.04.2

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username_UNIQUE` (`username`),
  UNIQUE KEY `email_UNIQUE` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'testuser','test@example.com','2023-10-01 12:00:00');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;


-- Dump completed on 2023-10-01 12:34:56
"""

    # Create a temporary test file with SQL dump content
    with tempfile.NamedTemporaryFile(delete=False, suffix=".sql") as tmp_file:
        tmp_file.write(sql_dump_content.encode("utf-8"))
        tmp_file_path = tmp_file.name

    try:
        upload_sql_db_dump_to_s3(tmp_file_path)

        find_response = basic_s3_client.list_objects_v2(
            Bucket="test_bucket", Prefix="dumps/"
        )

        assert len(find_response["Contents"]) == 1

        saved_file_name = find_response["Contents"][0]["Key"]
        assert saved_file_name == f"dumps/{os.path.basename(tmp_file_path)}"

        get_response = basic_s3_client.get_object(
            Bucket="test_bucket", Key=saved_file_name
        )
        uploaded_content = get_response["Body"].read().decode("utf-8")

        assert uploaded_content == sql_dump_content

    finally:
        # Cleanup in case the test fails
        if Path(tmp_file_path).exists():
            Path(tmp_file_path).unlink()


CSV_CONTENT = b"name,value\nfoo,1\nbar,2\n"


@patch.dict(os.environ, {"CSV_UPLOAD_BUCKET": "test_bucket"})
def test_upload_csv_to_s3_success(basic_s3_client):
    key = upload_csv_to_s3(io.BytesIO(CSV_CONTENT), "test.csv")

    assert key.startswith("csv-uploads/")
    assert key.endswith(".csv")

    get_response = basic_s3_client.get_object(Bucket="test_bucket", Key=key)
    assert get_response["Body"].read() == CSV_CONTENT
    assert get_response["ContentType"] == "text/csv"


@patch.dict(os.environ, {"CSV_UPLOAD_BUCKET": "test_bucket"})
def test_upload_csv_to_s3_generates_unique_keys(basic_s3_client):
    first_key = upload_csv_to_s3(io.BytesIO(CSV_CONTENT), "test.csv")
    second_key = upload_csv_to_s3(io.BytesIO(CSV_CONTENT), "test2.csv")

    assert first_key != second_key

    find_response = basic_s3_client.list_objects_v2(
        Bucket="test_bucket", Prefix="csv-uploads/"
    )
    assert len(find_response["Contents"]) == 2


@patch.dict(os.environ, {"CSV_UPLOAD_BUCKET": "non-existent-bucket"})
def test_upload_csv_to_s3_when_bucket_missing(basic_s3_client):
    with pytest.raises(ClientError) as e:
        upload_csv_to_s3(io.BytesIO(CSV_CONTENT), "test.csv")

    assert e.value.response["Error"]["Code"] == "NoSuchBucket"
