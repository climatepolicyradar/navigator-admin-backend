import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Tuple
from urllib.parse import quote_plus, urlsplit

import boto3
from botocore.exceptions import ClientError
from pydantic import AnyHttpUrl, BaseModel

import app.service.notification as notification_service
from app.clients.aws.client import AWSClient
from app.errors import RepositoryError

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)


class S3UploadContext(BaseModel):
    bucket_name: str
    object_name: str


def _encode_characters_in_path(s3_path: str) -> str:
    """
    Encode special characters in S3 URL path component to fix broken CDN links.

    :param s3_path: The s3 URL path component in which to fix encodings
    :returns: A URL path component containing encoded characters
    """
    encoded_path = "/".join([quote_plus(c) for c in s3_path.split("/")])
    return encoded_path


def s3_to_cdn_url(s3_url: AnyHttpUrl, cdn_url: AnyHttpUrl) -> AnyHttpUrl:
    """
    Converts an S3 url to a CDN url

    :param str s3_url: S3 url to convert
    :param str cdn_url: CDN url prefix to use
    :return str: the resultant URL
    """
    converted_cdn_url = re.sub(
        r"https:\/\/.*\.s3\..*\.amazonaws.com", str(cdn_url), str(s3_url)
    )
    split_url = urlsplit(converted_cdn_url)
    new_path = _encode_characters_in_path(split_url.path)

    # Ensures the path starts with a single slash
    new_path = "/" + new_path.lstrip("/")
    return AnyHttpUrl(f"{split_url.scheme}://{split_url.hostname}{new_path}")


def generate_pre_signed_url(
    client: AWSClient, bucket_name: str, key: str
) -> AnyHttpUrl:
    """
    Generate a pre-signed URL to an object for file uploads

    :return str: A pre-signed URL
    """
    try:
        url = client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": bucket_name,
                "Key": key,
            },
        )
        return AnyHttpUrl(url)
    except ClientError:
        msg = f"Request to create pre-signed URL for {key} failed"
        raise RepositoryError(msg)


def get_s3_url(region: str, bucket: str, key: str) -> AnyHttpUrl:
    """
    Formats up the s3 url from the parameters.

    :param str region: AWS region
    :param str bucket: AWS bucket
    :param str key: AWS key for object in S3
    :return str: the s3 url
    """
    return AnyHttpUrl(f"https://{bucket}.s3.{region}.amazonaws.com/{key}")


def upload_json_to_s3(
    s3_client: AWSClient, context: S3UploadContext, json_data: dict[str, Any]
) -> None:
    """
    Upload a JSON file to S3

    :param S3UploadContext context: The context of the upload.
    :param dict[str, Any] json_data: The json data to be uploaded to S3.
    :raises Exception: on any error when uploading the file to S3.
    """
    _LOGGER.info(f"Uploading {context.object_name} to: {context.bucket_name}")
    try:
        s3_client.put_object(
            Bucket=context.bucket_name,
            Key=context.object_name,
            Body=json.dumps(json_data),
            ContentType="application/json",
        )
        _LOGGER.info(
            f"🎉 Successfully uploaded JSON to S3: {context.bucket_name}/{context.object_name}"
        )
    except Exception as e:
        _LOGGER.error(f"💥 Failed to upload JSON to S3:{e}]")
        raise


def upload_bulk_import_json_to_s3(
    import_id: str, corpus_import_id: str, data: dict[str, Any]
) -> None:
    """
    Upload an bulk import JSON file to S3

    :param str import_id: The uuid of the bulk import action.
    :param str corpus_import_id: The id of the corpus the bulk import data belongs to.
    :param dict[str, Any] json_data: The bulk import json data to be uploaded to S3.
    """
    bulk_import_upload_bucket = os.environ["BULK_IMPORT_BUCKET"]
    current_timestamp = datetime.now().strftime("%m-%d-%YT%H:%M:%S")

    filename = f"{import_id}-{corpus_import_id}-{current_timestamp}.json"

    s3_client = boto3.client("s3")

    context = S3UploadContext(
        bucket_name=bulk_import_upload_bucket,
        object_name=filename,
    )
    upload_json_to_s3(s3_client, context, data)


def upload_sql_db_dump_to_s3(dump_file: str) -> None:
    """
    Upload the database dump to S3 and clean up local file.

    Args:
        dump_file (str): Path to the dump file
    """
    s3_client = boto3.client("s3")
    bucket_name = os.environ.get("DATABASE_DUMP_BUCKET")

    if not bucket_name:
        raise ValueError("DATABASE_DUMP_BUCKET environment variable not set")

    s3_key = f"dumps/{os.path.basename(dump_file)}"
    dump_path = Path(dump_file)

    try:
        if not dump_path.exists():
            raise FileNotFoundError(f"Dump file not found: {dump_file}")

        _LOGGER.info(f"🚀 Uploading {dump_file} to S3 bucket {bucket_name}")

        with dump_path.open("rb") as f:
            s3_client.upload_fileobj(f, bucket_name, s3_key)

        _LOGGER.info("🎉 Database Dump upload completed successfully")

    except Exception as e:
        _LOGGER.exception(f"💥 Upload failed {e}")
        notification_service.send_notification("💥 Database Dump upload failed.")
        raise e


def _get_object_url_in_cdn(
    client: AWSClient, key: str, bucket_name: str, cdn_url: AnyHttpUrl
) -> AnyHttpUrl:
    url = get_s3_url(client.meta.region_name, bucket_name, key)
    return s3_to_cdn_url(url, cdn_url)


def get_upload_details(
    client: AWSClient, key: str, bucket_name: str, cdn_url: AnyHttpUrl
) -> Tuple[AnyHttpUrl, AnyHttpUrl]:
    return (
        generate_pre_signed_url(client, bucket_name, key),
        _get_object_url_in_cdn(client, key, bucket_name, cdn_url),
    )


# TODO: add more s3 functions like listing and reading files here
