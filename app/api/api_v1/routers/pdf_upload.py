import logging
import os

from fastapi import APIRouter, HTTPException, status

from app.errors import PreSignedUrlError, ValidationError
from app.service.pdf_upload import (
    PdfUploadDTO,
    PdfUploadRequestDTO,
    get_pdf_upload_urls,
)

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

pdf_upload_router = r = APIRouter()


@r.post("/pdf-upload", response_model=list[PdfUploadDTO])
async def get_presigned_urls_for_pdf_uploads(
    body: PdfUploadRequestDTO,
) -> list[PdfUploadDTO]:
    """Get presigned URLs for uploading PDFs.

    :param body: The files to be uploaded
    :return: One upload URL set per file
    """
    _LOGGER.info(f"Getting upload URLs for {len(body.files)} PDF(s)")

    bucket = os.environ.get("DOCUMENT_STORE_PDF_UPLOAD_BUCKET")
    if not bucket:
        _LOGGER.error("DOCUMENT_STORE_PDF_UPLOAD_BUCKET environment variable not set")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Missing required settings for PDF upload",
        )

    try:
        return get_pdf_upload_urls(body, bucket)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except PreSignedUrlError as e:
        _LOGGER.error(f"Error creating PDF upload URLs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.message
        )
