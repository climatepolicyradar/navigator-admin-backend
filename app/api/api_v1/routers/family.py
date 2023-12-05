"""
Endpoints for managing the Family entity.

It was considered to create a "service" layer that would use the repo 
directly.  However, this API has little / no logic in so the service 
layer would just pass through directly to the repo. So the approach
implemented directly accesses the "repository" layer.
"""
import logging
from typing import Union, cast

from fastapi import APIRouter, HTTPException, Request, status

import app.service.family as family_service
from app.errors import RepositoryError, ValidationError
from app.model.family import FamilyCreateDTO, FamilyReadDTO, FamilyWriteDTO

families_router = r = APIRouter()

_LOGGER = logging.getLogger(__name__)


@r.get(
    "/families/{import_id}",
    response_model=FamilyReadDTO,
)
async def get_family(
    import_id: str,
) -> FamilyReadDTO:
    """
    Returns a specific family given the import id.

    :param str import_id: Specified import_id.
    :raises HTTPException: If the family is not found a 404 is returned.
    :return FamilyDTO: returns a FamilyDTO of the family found.
    """
    try:
        family = family_service.get(import_id)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )

    if family is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Family not found: {import_id}",
        )

    return family


@r.get(
    "/families",
    response_model=list[FamilyReadDTO],
)
async def get_all_families() -> list[FamilyReadDTO]:
    """
    Returns all families

    :return FamilyDTO: returns a FamilyDTO of the family found.
    """
    return family_service.all()


@r.get(
    "/families/",
    response_model=list[FamilyReadDTO],
)
async def search_family(request: Request) -> list[FamilyReadDTO]:
    """
    Searches for families matching URL parameters ("q" by default).

    :param Request request: The fields to match against and the values
        to search for. Defaults to searching for "" in family titles and
        summaries.
    :raises HTTPException: If invalid fields passed a 400 is returned.
    :raises HTTPException: If nothing found a 404 is returned.
    :return list[FamilyDTO]: A list of matching families.
    """
    query_params: dict[str, Union[str, int]] = {
        k: request.query_params[k] for k in request.query_params.keys()
    }

    query_fields = query_params.keys()
    if len(query_fields) < 1:
        query_params = {"q": ""}

    VALID_PARAMS = ["q", "title", "description", "geography", "status", "max_results"]
    invalid_params = [x for x in query_fields if x not in VALID_PARAMS]
    if any(invalid_params):
        msg = f"Search parameters are invalid: {invalid_params}"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg,
        )

    if "q" in query_fields:
        if "title" in query_fields:
            query_params.pop("title")
        if "description" in query_fields:
            query_params.pop("description")

    DEFAULT_MAX_RESULTS = 500
    if "max_results" not in query_fields:
        query_params["max_results"] = DEFAULT_MAX_RESULTS
    else:
        if not isinstance(query_params["max_results"], int):
            try:
                query_params.update(
                    {"max_results": cast(int, query_params["max_results"])}
                )
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Maximum results must be an integer value",
                )

    try:
        families = family_service.search(query_params)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except TimeoutError:
        msg = "Request timed out fetching matching families. Try adjusting your query."
        _LOGGER.error(msg)
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=msg,
        )

    if len(families) == 0:
        _LOGGER.info(f"Families not found for terms: {query_params}")

    return families


@r.put(
    "/families/{import_id}",
    response_model=FamilyReadDTO,
)
async def update_family(
    request: Request,
    import_id: str,
    new_family: FamilyWriteDTO,
) -> FamilyReadDTO:
    """
    Updates a specific family given the import id.

    :param str import_id: Specified import_id.
    :raises HTTPException: If the family is not found a 404 is returned.
    :return FamilyDTO: returns a FamilyDTO of the family updated.
    """
    try:
        family = family_service.update(import_id, request.state.user.email, new_family)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )

    if family is None:
        detail = f"Family not updated: {import_id}"
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

    return family


@r.post("/families", response_model=str, status_code=status.HTTP_201_CREATED)
async def create_family(
    request: Request,
    new_family: FamilyCreateDTO,
) -> str:
    """
    Creates a specific family given the import id.

    :raises HTTPException: If the family is not found a 404 is returned.
    :return FamilyDTO: returns a FamilyDTO of the new family.
    """
    try:
        family = family_service.create(new_family, request.state.user.email)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )

    return family


@r.delete(
    "/families/{import_id}",
)
async def delete_family(
    import_id: str,
) -> None:
    """
    Deletes a specific family given the import id.

    :param str import_id: Specified import_id.
    :raises HTTPException: If the family is not found a 404 is returned.
    """
    try:
        family_deleted = family_service.delete(import_id)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )

    if not family_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Family not deleted: {import_id}",
        )
