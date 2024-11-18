import json
import logging
import os
import re
from datetime import datetime
from typing import Any
from urllib.parse import quote_plus, urlsplit

import boto3
from botocore.exceptions import ClientError
from pydantic import BaseModel

from app.clients.aws.client import AWSClient
from app.errors import RepositoryError

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)


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


def s3_to_cdn_url(s3_url: str, cdn_url: str) -> str:
    """
    Converts an S3 url to a CDN url

    :param str s3_url: S3 url to convert
    :param str cdn_url: CDN url prefix to use
    :return str: the resultant URL
    """
    converted_cdn_url = re.sub(r"https:\/\/.*\.s3\..*\.amazonaws.com", cdn_url, s3_url)
    split_url = urlsplit(converted_cdn_url)
    new_path = _encode_characters_in_path(split_url.path)
    # CDN URL should include only scheme, host & modified path
    return f"{split_url.scheme}://{split_url.hostname}{new_path}"


def generate_pre_signed_url(client: AWSClient, bucket_name: str, key: str) -> str:
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
        return url
    except ClientError:
        msg = f"Request to create pre-signed URL for {key} failed"
        raise RepositoryError(msg)


def get_s3_url(region: str, bucket: str, key: str) -> str:
    """
    Formats up the s3 url from the parameters.

    :param str region: AWS region
    :param str bucket: AWS bucket
    :param str key: AWS key for object in S3
    :return str: the s3 url
    """
    return f"https://{bucket}.s3.{region}.amazonaws.com/{key}"


def upload_json_to_s3(
    s3_client: AWSClient, context: S3UploadContext, json_data: dict[str, Any]
) -> None:
    """
    Upload a JSON file to S3

    :param S3UploadContext context: The context of the upload.
    :param dict[str, Any] json_data: The json data to be uploaded to S3.
    :raises Exception: on any error when uploading the file to S3.
    """
    try:
        response = s3_client.put_object(
            Bucket=context.bucket_name,
            Key=context.object_name,
            Body=json.dumps(json_data),
            ContentType="application/json",
        )
        _LOGGER.debug(f"Response from S3 client: {response}")
        _LOGGER.info(
            f"🎉 Successfully uploaded JSON to S3: {context.bucket_name}/{context.object_name}"
        )
    except Exception as e:
        _LOGGER.error(f"💥 Failed to upload JSON to S3:{e}]")
        raise


def upload_ingest_json_to_s3(
    ingest_id: str, corpus_import_id: str, data: dict[str, Any]
) -> None:
    """
    Upload an ingest JSON file to S3

    :param str ingest_id: The uuid of the ingest action.
    :param str corpus_import_id: The import_id of the corpus the ingest data belongs to.
    :param dict[str, Any] json_data: The ingest json data to be uploaded to S3.
    """
    _LOGGER.info(f"Uploading file to: {os.getenv('BULK_IMPORT_BUCKET')}")
    ingest_upload_bucket = os.environ["BULK_IMPORT_BUCKET"]
    current_timestamp = datetime.now().strftime("%m-%d-%YT%H:%M:%S")

    filename = f"{ingest_id}-{corpus_import_id}-{current_timestamp}.json"

    if ingest_upload_bucket == "skip":
        os.makedirs("bulk_import_results", exist_ok=True)
        with open(f"bulk_import_results/{filename}", "w") as file:
            json.dump(data, file, indent=4)
        return

    s3_client = boto3.client("s3", region_name="eu-west-2")

    context = S3UploadContext(
        bucket_name=ingest_upload_bucket,
        object_name=filename,
    )
    upload_json_to_s3(s3_client, context, data)


# TODO: add more s3 functions like listing and reading files here
