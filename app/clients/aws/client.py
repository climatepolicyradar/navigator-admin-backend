import json
import logging
import os
from typing import Any

import boto3
import botocore.client
from pydantic import BaseModel

from app.model.aws_config import AWSConfig

logger = logging.getLogger(__name__)

_AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")
_AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
_AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
_SIGNATURE_VERSION = "s3v4"

AWSClient = Any


class S3UploadConfig(BaseModel):
    bucket_name: str
    object_name: str


def _get_client_from_config(config: AWSConfig) -> AWSClient:
    return boto3.client(
        config.service_name,
        aws_access_key_id=config.aws_access_key_id,
        aws_secret_access_key=config.aws_secret_access_key,
        config=botocore.client.Config(
            signature_version=config.signature_version, region_name=config.region_name
        ),
    )


def get_s3_client() -> AWSClient:
    """Get an AWS S3 client"""
    config = AWSConfig(
        service_name="s3",
        aws_access_key_id=_AWS_ACCESS_KEY_ID,
        aws_secret_access_key=_AWS_SECRET_ACCESS_KEY,
        signature_version=_SIGNATURE_VERSION,
        region_name=_AWS_REGION,
    )
    return _get_client_from_config(config)


def upload_json_to_s3(config: S3UploadConfig, json_data: dict) -> None:
    """
    Upload a JSON file to S3

    """
    s3_client = get_s3_client()
    try:
        s3_client.put_object(
            Bucket=config.bucket_name,
            Key=config.object_name,
            Body=json.dumps(json_data),
            ContentType="application/json",
        )
        logger.info(
            "🎉 Successfully uploaded JSON to S3: %s/%s",
            config.bucket_name,
            config.object_name,
        )
    except Exception as e:
        logger.error("💥 Failed to upload JSON to S3: %s", e)
        raise


# Example usage:
# upload_json_to_s3(S3UploadConfig(bucket_name="my-bucket", object_name="data.json"), {"key": "value"})
