"""Endpoints for managing the Document entity."""
import logging
from fastapi import APIRouter, HTTPException, status
from app.errors import RepositoryError, ValidationError
from app.model.document import (
    DocumentReadDTO,
)

import app.service.document as document_service

document_router = r = APIRouter()

_LOGGER = logging.getLogger(__name__)


@r.get(
    "/documents/{import_id}",
    response_model=DocumentReadDTO,
)
async def get_document(
    import_id: str,
) -> DocumentReadDTO:
    """
    Returns a specific document given the import id.

    :param str import_id: Specified import_id.
    :raises HTTPException: If the document is not found a 404 is returned.
    :return DocumentDTO: returns a DocumentDTO of the document found.
    """
    try:
        document = document_service.get(import_id)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {import_id}",
        )

    return document


@r.get(
    "/documents",
    response_model=list[DocumentReadDTO],
)
async def get_all_documents() -> list[DocumentReadDTO]:
    """
    Returns all documents

    :return DocumentDTO: returns a DocumentDTO of the document found.
    """
    try:
        return document_service.all()
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )


@r.get(
    "/documents/",
    response_model=list[DocumentReadDTO],
)
async def search_document(q: str = "") -> list[DocumentReadDTO]:
    """
    Searches for documents matching the "q" URL parameter.

    :param str q: The string to match, defaults to ""
    :raises HTTPException: If nothing found a 404 is returned.
    :return list[DocumentDTO]: A list of matching documents.
    """
    try:
        documents = document_service.search(q)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )

    if documents is None or len(documents) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documents not found for term: {q}",
        )

    return documents


@r.post(
    "/documents", response_model=DocumentReadDTO, status_code=status.HTTP_201_CREATED
)
async def create_document(
    new_document: DocumentReadDTO,
) -> DocumentReadDTO:
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

    # See PDCT-305
    #
    # TODO: return Tuple[DocumentReadDTO, Optional[DocumentUploadResponse]]
    # if upload_request is None:
    #     return document, None

    # try:
    #     upload_details = document_service.get_upload_details(
    #         upload_request.filename, upload_request.overwrite
    #     )

    #     upload_response = DocumentUploadResponse(
    #         presigned_upload_url=upload_details[0], cdn_url=upload_details[1]
    #     )
    # except RepositoryError as e:
    #     _LOGGER.error(e.message)
    #     raise HTTPException(
    #         status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
    #     )

    return document
