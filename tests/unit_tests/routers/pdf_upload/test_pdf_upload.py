import os
from unittest.mock import patch

from fastapi import status
from fastapi.testclient import TestClient

from app.errors import PreSignedUrlError

UPLOAD_URL = "/api/v1/pdf-upload"
PATCH_TARGET = "app.api.api_v1.routers.pdf_upload.get_pdf_upload_urls"


def test_pdf_upload_when_not_authenticated(client: TestClient):
    response = client.post(UPLOAD_URL)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_pdf_upload_when_admin_non_super(client: TestClient, admin_user_header_token):
    response = client.post(
        UPLOAD_URL,
        headers=admin_user_header_token,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


VALID_BODY = {
    "files": [
        {"file_name": "test.pdf", "size": 1024, "content_type": "application/pdf"}
    ]
}
UPLOAD_RESPONSE = [
    {
        "file_name": "test.pdf",
        "key": "2026-10-12/test.pdf",
        "presigned_upload_url": "https://example.com/upload",
    }
]


@patch.dict(os.environ, {"DOCUMENT_STORE_PDF_UPLOAD_BUCKET": "test-pdf-bucket"})
@patch(PATCH_TARGET, return_value=UPLOAD_RESPONSE)
def test_pdf_upload_when_ok(upload_mock, client: TestClient, superuser_header_token):
    response = client.post(UPLOAD_URL, json=VALID_BODY, headers=superuser_header_token)

    upload_mock.assert_called_once()
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == UPLOAD_RESPONSE


@patch.dict(os.environ, {"DOCUMENT_STORE_PDF_UPLOAD_BUCKET": "test-pdf-bucket"})
def test_pdf_upload_when_s3_fails(client: TestClient, superuser_header_token):
    error = PreSignedUrlError("Request failed: s3 error")

    with patch(PATCH_TARGET, side_effect=error):
        response = client.post(
            UPLOAD_URL, json=VALID_BODY, headers=superuser_header_token
        )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Request failed: s3 error"}
