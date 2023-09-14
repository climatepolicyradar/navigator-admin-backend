import os
from typing import Tuple
from app.clients.aws.client import AWSClient
import app.clients.aws.s3bucket as s3_bucket


_CDN_URL: str = os.getenv("CDN_URL", "https://cdn.climatepolicyradar.org")
_BUCKET_NAME = os.getenv("S3_DOCUMENT_BUCKET", "test-document-bucket")


def _get_cdn_url(client: AWSClient, key: str) -> str:
    url = s3_bucket.get_s3_url(client.meta.region_name, _BUCKET_NAME, key)
    return s3_bucket.s3_to_cdn_url(url, _CDN_URL)


def get_upload_details(client: AWSClient, key: str) -> Tuple[str, str]:
    return (
        s3_bucket.generate_pre_signed_url(client, _BUCKET_NAME, key),
        _get_cdn_url(client, key),
    )
