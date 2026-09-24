import io
from unittest.mock import patch

from botocore.exceptions import ClientError
from fastapi import status
from fastapi.testclient import TestClient

UPLOAD_URL = "/api/v1/csv-upload"
PATCH_TARGET = "app.api.api_v1.routers.csv_upload.upload_csv_to_s3"
CSV_CONTENT = b"name,value\nfoo,1\nbar,2\n"
TEST_KEY = "csv-uploads/test-key.csv"


def build_csv_file(content: bytes = CSV_CONTENT):
    return ("test.csv", io.BytesIO(content), "text/csv")


def test_csv_upload_when_not_authenticated(client: TestClient):
    response = client.post(UPLOAD_URL)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@patch(PATCH_TARGET, return_value=TEST_KEY)
def test_csv_upload_when_ok(upload_mock, client: TestClient, superuser_header_token):
    response = client.post(
        UPLOAD_URL,
        files={"file": build_csv_file()},
        headers=superuser_header_token,
    )

    upload_mock.assert_called_once()
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {
        "message": "CSV uploaded successfully",
        "key": TEST_KEY,
    }


def test_csv_upload_when_s3_fails(client: TestClient, superuser_header_token):
    s3_error = ClientError(
        {"Error": {"Code": "NoSuchBucket", "Message": "bucket internals"}},
        "PutObject",
    )

    with patch(PATCH_TARGET, side_effect=s3_error):
        response = client.post(
            UPLOAD_URL,
            files={"file": build_csv_file()},
            headers=superuser_header_token,
        )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json().get("detail") == "Failed to upload file to S3"
    assert "bucket internals" not in response.text


def test_csv_upload_when_no_file(client: TestClient, superuser_header_token):
    with patch(PATCH_TARGET) as upload_mock:
        response = client.post(UPLOAD_URL, headers=superuser_header_token)

    upload_mock.assert_not_called()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
