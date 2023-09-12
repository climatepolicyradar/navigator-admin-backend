"""Endpoints for managing the Collection entity."""
import logging
from fastapi import APIRouter, HTTPException, status
from app.errors import RepositoryError, ValidationError

from app.model.collection import CollectionDTO
import app.service.collection as collection_service

collections_router = r = APIRouter()

_LOGGER = logging.getLogger(__name__)


@r.get(
    "/collections/{import_id}",
    response_model=CollectionDTO,
)
async def get_collection(
    import_id: str,
) -> CollectionDTO:
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
    response_model=list[CollectionDTO],
)
async def get_all_collections() -> list[CollectionDTO]:
    """
    Returns all collections

    :return CollectionDTO: returns a CollectionDTO of the collection found.
    """
    return collection_service.all()


@r.get(
    "/collections/",
    response_model=list[CollectionDTO],
)
async def search_collection(q: str = "") -> list[CollectionDTO]:
    """
    Searches for collections matching the "q" URL parameter.

    :param str q: The string to match, defaults to ""
    :raises HTTPException: If nothing found a 404 is returned.
    :return list[CollectionDTO]: A list of matching collections.
    """
    collections = collection_service.search(q)
    if collections is None or len(collections) == 0:
        raise HTTPException(
            status_code=404, detail=f"collections not found for term: {q}"
        )

    return collections


@r.put(
    "/collections",
    response_model=CollectionDTO,
)
async def update_collection(
    new_collection: CollectionDTO,
) -> CollectionDTO:
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
    "/collections", response_model=CollectionDTO, status_code=status.HTTP_201_CREATED
)
async def create_collection(
    new_collection: CollectionDTO,
) -> CollectionDTO:
    """
    Creates a specific collection given the import id.

    :raises HTTPException: If the collection is not found a 404 is returned.
    :return CollectionDTO: returns a CollectionDTO of the new collection.
    """
    try:
        collection = collection_service.create(new_collection)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )

    if collection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection not created: {new_collection.import_id}",
        )

    return collection


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
