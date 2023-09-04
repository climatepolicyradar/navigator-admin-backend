"""Endpoints for managing the Collection entity."""
import logging
from fastapi import APIRouter, HTTPException
from app.errors.repository_error import RepositoryError
from app.errors.validation_error import ValidationError
from app.model.collection import CollectionDTO

import app.service.collection as collection_service

collection_router = r = APIRouter()

_LOGGER = logging.getLogger(__name__)


@r.get(
    "/collection/{import_id}",
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
        raise HTTPException(status_code=400, detail=e.message)
    except RepositoryError as e:
        raise HTTPException(status_code=503, detail=e.message)

    if collection is None:
        raise HTTPException(
            status_code=404, detail=f"Collection not found: {import_id}"
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


# @r.get(
#     "/collections/",
#     response_model=list[CollectionDTO],
# )
# async def search_collection(q: str = "") -> list[CollectionDTO]:
#     """
#     Searches for collections matching the "q" URL parameter.

#     :param str q: The string to match, defaults to ""
#     :raises HTTPException: If nothing found a 404 is returned.
#     :return list[CollectionDTO]: A list of matching collections.
#     """
#     collections = collection_service.search(q)
#     if collections is None or len(collections) == 0:
#         raise HTTPException(status_code=404,
# detail=f"collections not found for term: {q}")

#     return collections
