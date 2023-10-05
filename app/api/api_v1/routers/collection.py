"""Endpoints for managing the Collection entity."""
import logging
from fastapi import APIRouter, HTTPException, status
from app.errors import RepositoryError, ValidationError

from app.model.collection import (
    CollectionReadDTO,
    CollectionWriteDTO,
    CollectionCreateDTO,
)
import app.service.collection as collection_service

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
async def search_collection(q: str = "") -> list[CollectionReadDTO]:
    """
    Searches for collections matching the "q" URL parameter.

    :param str q: The string to match, defaults to ""
    :raises HTTPException: If nothing found a 404 is returned.
    :return list[CollectionDTO]: A list of matching collections.
    """
    try:
        collections = collection_service.search(q)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )

    if collections is None or len(collections) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collections not found for term: {q}",
        )

    return collections


@r.put(
    "/collections",
    response_model=CollectionReadDTO,
)
async def update_collection(
    new_collection: CollectionWriteDTO,
) -> CollectionReadDTO:
    """
    Updates a specific collection given the import id.

    :param str import_id: Specified import_id.
    :raises HTTPException: If the collection is not found a 404 is returned.
    :return CollectionDTO: returns a CollectionDTO of the collection updated.
    """
    try:
        collection = collection_service.update(new_collection)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )

    if collection is None:
        detail = f"Collection not updated: {new_collection.import_id}"
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

    return collection


@r.post(
    "/collections",
    response_model=str,
    status_code=status.HTTP_201_CREATED,
)
async def create_collection(
    new_collection: CollectionCreateDTO,
) -> str:
    """
    Creates a specific collection given the import id.

    :raises HTTPException: If the collection is not found a 404 is returned.
    :return str: returns the import_id of the new collection.
    """
    try:
        return collection_service.create(new_collection)
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
