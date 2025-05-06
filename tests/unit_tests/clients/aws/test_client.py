import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from botocore.exceptions import ClientError

from app.clients.aws.s3bucket import (
    S3UploadContext,
    upload_bulk_import_json_to_s3,
    upload_json_to_s3,
    upload_sql_db_dump_to_s3,
)


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
