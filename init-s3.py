import boto3

# trunk-ignore(bandit/B106)
s3_client = boto3.client(
    "s3",
    endpoint_url="http://localhost:4566",
    aws_access_key_id="test",
    aws_secret_access_key="test",
)

s3_client.create_bucket(Bucket="bulk-import-bucket")
