import logging
import os
from typing import Any

import boto3
import botocore.client

from app.model.aws_config import AWSConfig

logger = logging.getLogger(__name__)

_AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")
_AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
_AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
_SIGNATURE_VERSION = "s3v4"

AWSClient = Any


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
