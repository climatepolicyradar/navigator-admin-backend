import logging
import os

import boto3

_LOGGER = logging.getLogger(__name__)

try:
    s3_client = boto3.client(
        "s3",
        endpoint_url=os.environ["AWS_ENDPOINT_URL"],
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    )

    s3_client.create_bucket(Bucket=os.environ["BULK_IMPORT_BUCKET"])
except Exception as e:
    _LOGGER.error(e)
