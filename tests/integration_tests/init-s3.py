import logging
import os

import boto3
from botocore.exceptions import BotoCoreError, ClientError

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)


def create_s3_bucket() -> None:
    """
    Create an S3 bucket using environment variables for configuration.

    Raises:
        AssertionError: If a required environment variable is missing.
        BotoCoreError, ClientError: If there's an error with boto3 operation.
    """
    required_vars = [
        "AWS_ENDPOINT_URL",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "BULK_IMPORT_BUCKET",
    ]
    missing_vars = [var for var in required_vars if var not in os.environ]
    assert (
        not missing_vars
    ), f"🔥 Required environment variable(s) missing: {', '.join(missing_vars)}"

    try:
        s3_client = boto3.client(
            "s3",
            endpoint_url=os.environ["AWS_ENDPOINT_URL"],
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        )

        s3_client.create_bucket(Bucket=os.environ["BULK_IMPORT_BUCKET"])

        _LOGGER.info("🎉 Bucket created successfully")

    except (BotoCoreError, ClientError) as e:
        _LOGGER.error(f"🔥 Error: {e}")


create_s3_bucket()
