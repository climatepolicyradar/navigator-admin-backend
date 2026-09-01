from typing import Optional

from pydantic import BaseModel


class AWSConfig(BaseModel):
    """
    Config object used for creating boto3 client.

    See:
    - boto3.client()
    - botocore.client.Config
    """

    service_name: str
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    signature_version: str
    region_name: str
