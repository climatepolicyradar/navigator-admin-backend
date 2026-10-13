import re
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Self
from urllib.parse import quote

from pydantic import AnyHttpUrl, BaseModel, Field, model_validator

from app.clients.aws.client import get_s3_client
from app.clients.aws.s3bucket import PDF_CONTENT_TYPE, generate_pdf_pre_signed_url

MAX_FILES_PER_REQUEST = 10


class PdfUploadFileDTO(BaseModel):
    file_name: str
    size: int
    content_type: str

    @model_validator(mode="after")
    def must_be_pdf(self) -> Self:
        if (
            not self.file_name.lower().endswith(".pdf")
            or self.content_type != PDF_CONTENT_TYPE
        ):
            raise ValueError(f"{self.file_name} is not a PDF")
        return self


class PdfUploadRequestDTO(BaseModel):
    files: list[PdfUploadFileDTO] = Field(
        min_length=1, max_length=MAX_FILES_PER_REQUEST
    )
    # TODO: folder: PdfUploadFolder = PdfUploadFolder.DEFAULT


class PdfUploadDTO(BaseModel):
    file_name: str
    key: str
    destination_url: str
    presigned_upload_url: AnyHttpUrl


class PdfUploadFolder(str, Enum):
    """Allowed destination folders. v2: add members here."""


def _safe_pdf_name(name: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(name).stem).strip("._") or "document"
    return f"{stem[:100]}.pdf"


def _destination_url(bucket: str, region: str, key: str) -> str:
    return f"https://{bucket}.s3.{region}.amazonaws.com/{quote(key, safe='/')}"


def get_pdf_upload_urls(
    request: PdfUploadRequestDTO,
    bucket: str,
    folder: PdfUploadFolder | None = None,
) -> list[PdfUploadDTO]:
    """Get presigned URLs for uploading one or more PDFs.

    :param request: The files to upload
    :param bucket: The S3 bucket to upload to
    :param folder: Destination
    :return: One upload DTO per file, in the same order as the request
    """

    client = get_s3_client()
    region = client.meta.region_name

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
                destination_url=_destination_url(bucket, region, key),
                presigned_upload_url=generate_pdf_pre_signed_url(client, bucket, key),
            )
        )
    return uploads
