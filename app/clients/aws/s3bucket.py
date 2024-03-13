import re
from urllib.parse import quote_plus, urlsplit

from botocore.exceptions import ClientError

from app.clients.aws.client import AWSClient
from app.errors import RepositoryError


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


# TODO: add more s3 functions like listing and reading files here
