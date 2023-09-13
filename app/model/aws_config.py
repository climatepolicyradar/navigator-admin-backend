from pydantic import BaseModel


class AWSConfig(BaseModel):
    """
    Config object used for creating boto3 client.

    See:
    - boto3.client()
    - botocore.client.Config
    """

    service_name: str
    aws_access_key_id: str
    aws_secret_access_key: str
    signature_version: str
    region_name: str
