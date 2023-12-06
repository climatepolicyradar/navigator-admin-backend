"""Endpoints for managing the Collection entity."""
import logging

from fastapi import APIRouter, HTTPException, Request, status

import app.service.collection as collection_service
from app.api.api_v1.query_params import (
    get_query_params_as_dict,
    set_default_query_params,
    validate_query_params,
)
from app.errors import RepositoryError, ValidationError
from app.model.collection import (
    CollectionCreateDTO,
    CollectionReadDTO,
    CollectionWriteDTO,
)

collections_router = r = APIRouter()

_LOGGER = logging.getLogger(__name__)


@r.get(
    "/collections/{import_id}",
    response_model=CollectionReadDTO,
)
async def get_collection(
    import_id: str,
) -> CollectionReadDTO:
    """
    Returns a specific collection given the import id.

    :param str import_id: Specified import_id.
    :raises HTTPException: If the collection is not found a 404 is returned.
    :return CollectionDTO: returns a CollectionDTO of the collection found.
    """
    try:
        collection = collection_service.get(import_id)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )

    if collection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection not found: {import_id}",
        )

    return collection


@r.get(
    "/collections",
    response_model=list[CollectionReadDTO],
)
async def get_all_collections() -> list[CollectionReadDTO]:
    """
    Returns all collections

    :return CollectionDTO: returns a CollectionDTO of the collection found.
    """
    try:
        return collection_service.all()
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )


@r.get(
    "/collections/",
    response_model=list[CollectionReadDTO],
)
async def search_collection(request: Request) -> list[CollectionReadDTO]:
    """
    Searches for collections matching URL parameters ("q" by default).

    :param Request request: The fields to match against and the values
        to search for. Defaults to searching for "" in collection titles
        and summaries.
    :raises HTTPException: If invalid fields passed a 400 is returned.
    :raises HTTPException: If a DB error occurs a 503 is returned.
    :raises HTTPException: If the search request times out a 408 is
        returned.
    :return list[CollectionReadDTO]: A list of matching collections
        (which can be empty).
    """

    query_params = get_query_params_as_dict(request.query_params)

    query_params = set_default_query_params(query_params)

    VALID_PARAMS = ["q", "max_results"]
    validate_query_params(query_params, VALID_PARAMS)

    try:
        collections = collection_service.search(query_params)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )
    except TimeoutError:
        msg = (
            "Request timed out fetching matching collections. Try adjusting your query."
        )
        _LOGGER.error(msg)
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=msg,
        )

    if len(collections) == 0:
        _LOGGER.info(f"Collections not found for terms: {query_params}")

    return collections


@r.put(
    "/collections/{import_id}",
    response_model=CollectionReadDTO,
)
async def update_collection(
    import_id: str,
    new_collection: CollectionWriteDTO,
) -> CollectionReadDTO:
    """
    Updates a specific collection given the import id.

    :param str import_id: Specified import_id.
    :raises HTTPException: If the collection is not found a 404 is returned.
    :return CollectionDTO: returns a CollectionDTO of the collection updated.
    """
    try:
        collection = collection_service.update(import_id, new_collection)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )

    if collection is None:
        detail = f"Collection not updated: {import_id}"
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

    return collection


@r.post(
    "/collections",
    response_model=str,
    status_code=status.HTTP_201_CREATED,
)
async def create_collection(
    request: Request,
    new_collection: CollectionCreateDTO,
) -> str:
    """
    Creates a specific collection given the import id.

    :raises HTTPException: If the collection is not found a 404 is returned.
    :return str: returns the import_id of the new collection.
    """
    try:
        return collection_service.create(new_collection, request.state.user.email)
    except ValidationError as e:
        _LOGGER.error(e.message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except RepositoryError as e:
        _LOGGER.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )


@r.delete(
    "/collections/{import_id}",
)
async def delete_collection(
    import_id: str,
) -> None:
    """
    Deletes a specific collection given the import id.

    :param str import_id: Specified import_id.
    :raises HTTPException: If the collection is not found a 404 is returned.
    """
    try:
        collection_deleted = collection_service.delete(import_id)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )

    if not collection_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection not deleted: {import_id}",
        )
