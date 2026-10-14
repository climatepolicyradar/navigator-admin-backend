import os
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from pydantic import AnyHttpUrl

from app.errors import PreSignedUrlError
from app.service.pdf_upload import (
    MAX_FILES_PER_REQUEST,
    PDF_CONTENT_TYPE,
    PdfUploadDTO,
)

URL = "/api/v1/pdf-upload"
PATCH_SERVICE = "app.api.api_v1.routers.pdf_upload.get_pdf_upload_urls"
BUCKET = "test-pdf-bucket"


def _file(
    name: str = "report.pdf",
    size: int = 1024,
    content_type: str = PDF_CONTENT_TYPE,
) -> dict:
    return {"file_name": name, "size": size, "content_type": content_type}


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


@patch.dict(os.environ, {"DOCUMENT_STORE_PDF_UPLOAD_BUCKET": BUCKET})
def test_pdf_upload_urls_returns_presigned_url_for_single_file(
    client: TestClient,
    superuser_header_token,
):

    mock_return = [
        PdfUploadDTO(
            file_name="report.pdf",
            key=f"{_today()}/report.pdf",
            destination_url="https://example.com/destination-url",
            presigned_upload_url=AnyHttpUrl("https://example.com/presigned-url"),
        )
    ]

    with patch(PATCH_SERVICE, return_value=mock_return):
        response = client.post(
            URL, json={"files": [_file("report.pdf")]}, headers=superuser_header_token
        )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body[0]["presigned_upload_url"] == "https://example.com/presigned-url"


@pytest.mark.parametrize(
    ("file_spec", "detail"),
    [
        pytest.param(
            _file("notes.txt"), "notes.txt is not a PDF", id="wrong-extension"
        ),
        pytest.param(
            _file(content_type="text/csv"),
            "report.pdf is not a PDF",
            id="wrong-content-type",
        ),
    ],
)
def test_pdf_upload_urls_returns_unprocessable_entity_for_invalid_file(
    client: TestClient,
    superuser_header_token,
    file_spec: dict,
    detail: str,
):
    response = client.post(
        URL, json={"files": [file_spec]}, headers=superuser_header_token
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    errors = response.json()["detail"]
    assert len(errors) == 1
    assert errors[0]["loc"] == ["body", "files", 0]
    assert detail in errors[0]["msg"]


@patch.dict(os.environ, {"DOCUMENT_STORE_PDF_UPLOAD_BUCKET": BUCKET})
def test_pdf_upload_urls_returns_unprocessable_entity_when_no_files(
    client: TestClient,
    superuser_header_token,
):
    response = client.post(URL, json={"files": []}, headers=superuser_header_token)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error = response.json()["detail"][0]
    assert error["loc"] == ["body", "files"]
    assert error["type"] == "too_short"


@patch.dict(os.environ, {"DOCUMENT_STORE_PDF_UPLOAD_BUCKET": BUCKET})
def test_pdf_upload_urls_returns_unprocessable_entity_when_too_many_files(
    client: TestClient,
    superuser_header_token,
):
    files = [_file(f"file_{i}.pdf") for i in range(MAX_FILES_PER_REQUEST + 1)]

    response = client.post(URL, json={"files": files}, headers=superuser_header_token)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error = response.json()["detail"][0]
    assert error["loc"] == ["body", "files"]
    assert error["type"] == "too_long"


@patch.dict(os.environ, {"DOCUMENT_STORE_PDF_UPLOAD_BUCKET": BUCKET})
def test_pdf_upload_urls_returns_unprocessable_entity_when_body_malformed(
    client: TestClient,
    superuser_header_token,
):
    response = client.post(URL, json={}, headers=superuser_header_token)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@patch.dict(os.environ, {"DOCUMENT_STORE_PDF_UPLOAD_BUCKET": BUCKET})
def test_pdf_upload_urls_returns_server_error_when_presigning_fails(
    client: TestClient,
    superuser_header_token,
):
    message = "Request to create pre-signed URL for x failed"

    with patch(PATCH_SERVICE, side_effect=PreSignedUrlError(message)):
        response = client.post(
            URL, json={"files": [_file()]}, headers=superuser_header_token
        )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": message}
