"""Endpoints for managing the Document entity."""
import logging
from typing import Optional, Tuple
from fastapi import APIRouter, HTTPException, status
from app.errors import RepositoryError, ValidationError
from app.model.document import (
    DocumentReadDTO,
    DocumentUploadRequest,
    DocumentUploadResponse,
)

import app.service.document as document_service

document_router = r = APIRouter()

_LOGGER = logging.getLogger(__name__)


@r.post(
    "/documents", response_model=DocumentReadDTO, status_code=status.HTTP_201_CREATED
)
async def create_document(
    new_document: DocumentReadDTO, upload_request: Optional[DocumentUploadRequest]
) -> Tuple[DocumentReadDTO, Optional[DocumentUploadResponse]]:
    """
    Creates a specific document given the import id.

    :raises HTTPException: If the document is not found a 404 is returned.
    :return DocumentDTO: returns a DocumentDTO of the new document.
    """
    try:
        document = document_service.create(new_document)
    except ValidationError as e:
        _LOGGER.error(e.message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except RepositoryError as e:
        _LOGGER.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not created: {new_document.import_id}",
        )

    if upload_request is None:
        return document, None

    try:
        upload_details = document_service.get_upload_details(
            upload_request.filename, upload_request.overwrite
        )

        upload_response = DocumentUploadResponse(
            presigned_upload_url=upload_details[0], cdn_url=upload_details[1]
        )
    except RepositoryError as e:
        _LOGGER.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )

    return document, upload_response
