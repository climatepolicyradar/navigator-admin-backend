"""Endpoints for managing the Document entity."""

import logging

from fastapi import APIRouter, HTTPException, Request, status

import app.service.document as document_service
from app.api.api_v1.query_params import (
    get_query_params_as_dict,
    set_default_query_params,
    validate_query_params,
)
from app.errors import RepositoryError, ValidationError
from app.model.document import DocumentCreateDTO, DocumentReadDTO, DocumentWriteDTO

document_router = r = APIRouter()

_LOGGER = logging.getLogger(__name__)


@r.get(
    "/documents/{import_id}",
    response_model=DocumentReadDTO,
)
async def get_document(import_id: str) -> DocumentReadDTO:
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
async def get_all_documents(request: Request) -> list[DocumentReadDTO]:
    """
    Returns all documents

    :param Request request: Request object.
    :return DocumentDTO: returns a DocumentDTO of the document found.
    """
    try:
        return document_service.all(request.state.user.email)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )


@r.get(
    "/documents/",
    response_model=list[DocumentReadDTO],
)
async def search_document(request: Request) -> list[DocumentReadDTO]:
    """
    Searches for documents matching URL parameters ("q" by default).

    :param Request request: The fields to match against and the values
        to search for. Defaults to searching for "" in document titles.
    :raises HTTPException: If invalid fields passed a 400 is returned.
    :raises HTTPException: If a DB error occurs a 503 is returned.
    :raises HTTPException: If the search request times out a 408 is
        returned.
    :return list[DocumentReadDTO]: A list of matching documents (which
        can be empty).
    """
    query_params = get_query_params_as_dict(request.query_params)

    query_params = set_default_query_params(query_params)

    VALID_PARAMS = ["q", "max_results"]
    validate_query_params(query_params, VALID_PARAMS)

    try:
        documents = document_service.search(query_params, request.state.user.email)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )
    except TimeoutError:
        msg = "Request timed out fetching matching documents. Try adjusting your query."
        _LOGGER.error(msg)
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=msg,
        )

    if len(documents) == 0:
        _LOGGER.info(f"Documents not found for terms: {query_params}")

    return documents


@r.put(
    "/documents/{import_id}",
    response_model=DocumentReadDTO,
)
async def update_document(
    import_id: str, new_document: DocumentWriteDTO
) -> DocumentReadDTO:
    """
    Updates a specific document given the import id.

    :param str import_id: Specified import_id.
    :raises HTTPException: If the document is not found a 404 is returned.
    :return DocumentDTO: returns a DocumentDTO of the document updated.
    """
    try:
        document = document_service.update(import_id, new_document)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )

    if document is None:
        detail = f"Document not updated: {import_id}"
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

    return document


@r.post(
    "/documents",
    response_model=str,
    status_code=status.HTTP_201_CREATED,
)
async def create_document(new_document: DocumentCreateDTO) -> str:
    """
    Creates a specific document given the values in DocumentCreateDTO.

    :raises HTTPException: If the document is not found a 404 is returned.
    :return str: returns a the import_id of the document created.
    """
    try:
        return document_service.create(new_document)
    except ValidationError as e:
        _LOGGER.error(e.message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except RepositoryError as e:
        _LOGGER.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
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


@r.delete(
    "/documents/{import_id}",
)
async def delete_document(request: Request, import_id: str) -> None:
    """
    Deletes a specific document given the import id.

    :param Request request: Request object.
    :param str import_id: Specified import_id.
    :raises HTTPException: If the document is not found a 404 is returned.
    """
    try:
        document_deleted = document_service.delete(import_id, request.state.user.email)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )

    if not document_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not deleted: {import_id}",
        )
