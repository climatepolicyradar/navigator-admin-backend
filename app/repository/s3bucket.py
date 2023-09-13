import app.clients.aws.client as aws_client
from botocore.exceptions import ClientError

from app.errors import RepositoryError


def generate_pre_signed_url(
    client: aws_client.AWSClient, bucket_name: str, key: str
) -> str:
    """
    Generate a pre-signed URL to an object for file uploads

    :param S3Document s3_document: A description of the document to create/update
    :return str: A pre-signed URL
    """
    client = aws_client.get_s3_client()
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


def create():
    pass


def all():
    pass
