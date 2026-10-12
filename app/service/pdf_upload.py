import os
import re
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from pydantic import AnyHttpUrl, BaseModel

from app.clients.aws.client import get_s3_client
from app.clients.aws.s3bucket import PDF_CONTENT_TYPE, generate_pdf_pre_signed_url
from app.errors import ValidationError

MAX_FILES_PER_REQUEST = 10


class PdfUploadFileDTO(BaseModel):
    file_name: str
    size: int
    content_type: str


class PdfUploadRequestDTO(BaseModel):
    files: list[PdfUploadFileDTO]
    # TODO: folder: PdfUploadFolder = PdfUploadFolder.DEFAULT


class PdfUploadDTO(BaseModel):
    file_name: str
    key: str
    presigned_upload_url: AnyHttpUrl


class PdfUploadFolder(str, Enum):
    """Allowed destination folders. v2: add members here."""


def _safe_pdf_name(name: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(name).stem).strip("._") or "document"
    return f"{stem[:100]}.pdf"


def _validate_request(request: PdfUploadRequestDTO) -> None:
    if not request.files or len(request.files) > MAX_FILES_PER_REQUEST:
        raise ValidationError(f"Provide between 1 and {MAX_FILES_PER_REQUEST} files")
    for f in request.files:
        if (
            not f.file_name.lower().endswith(".pdf")
            or f.content_type != PDF_CONTENT_TYPE
        ):
            raise ValidationError(f"{f.file_name} is not a PDF")


def get_pdf_upload_urls(
    request: PdfUploadRequestDTO,
    folder: PdfUploadFolder | None = None,
) -> list[PdfUploadDTO]:
    """Get presigned URLs for uploading one or more PDFs.

    :param request: The files to upload
    :param folder: Destination
    :return: One upload DTO per file, in the same order as the request
    """
    _validate_request(request)

    if "DOCUMENT_STORE_PDF_UPLOAD_BUCKET" not in os.environ:
        raise ValueError(
            "DOCUMENT_STORE_PDF_UPLOAD_BUCKET environment variable not set"
        )

    bucket = os.environ["DOCUMENT_STORE_PDF_UPLOAD_BUCKET"]
    client = get_s3_client()

    directory = (
        folder.value
        if folder is not None
        else datetime.now(timezone.utc).date().isoformat()
    )

    uploads = []
    for f in request.files:
        key = f"{directory}/{_safe_pdf_name(f.file_name)}"
        uploads.append(
            PdfUploadDTO(
                file_name=f.file_name,
                key=key,
                presigned_upload_url=generate_pdf_pre_signed_url(client, bucket, key),
            )
        )
    return uploads
