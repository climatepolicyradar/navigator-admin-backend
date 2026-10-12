from unittest.mock import patch

from botocore.exceptions import ClientError
from fastapi import status
from fastapi.testclient import TestClient

UPLOAD_URL = "/api/v1/pdf-upload"
PATCH_TARGET = "app.api.api_v1.routers.pdf_upload.get_pdf_upload_urls"
TEST_KEY = "pdf-uploads/test-key.pdf"


def test_pdf_upload_when_not_authenticated(client: TestClient):
    response = client.post(UPLOAD_URL)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_pdf_upload_when_admin_non_super(client: TestClient, admin_user_header_token):
    response = client.post(
        UPLOAD_URL,
        headers=admin_user_header_token,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@patch(
    PATCH_TARGET,
    return_value=[
        {"file_name": "test.pdf", "upload_url": "https://example.com/upload"}
    ],
)
def test_pdf_upload_when_ok(upload_mock, client: TestClient, superuser_header_token):
    response = client.post(
        UPLOAD_URL,
        json={"files": ["test.pdf"]},
        headers=superuser_header_token,
    )

    upload_mock.assert_called_once()
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {"file_name": "test.pdf", "upload_url": "https://example.com/upload"}
    ]


def test_pdf_upload_when_s3_fails(client: TestClient, superuser_header_token):
    s3_error = ClientError(
        {"Error": {"Code": "NoSuchBucket", "Message": "bucket internals"}},
        "PutObject",
    )

    with patch(PATCH_TARGET, side_effect=s3_error):
        response = client.post(
            UPLOAD_URL,
            json={"files": ["test.pdf"]},
            headers=superuser_header_token,
        )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json().get("detail") == "Failed to generate upload URLs"
    assert "bucket internals" not in response.text
