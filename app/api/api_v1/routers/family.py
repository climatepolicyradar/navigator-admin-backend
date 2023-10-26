"""
Endpoints for managing the Family entity.

It was considered to create a "service" layer that would use the repo 
directly.  However, this API has little / no logic in so the service 
layer would just pass through directly to the repo. So the approach
implemented directly accesses the "repository" layer.
"""
import logging
from fastapi import APIRouter, HTTPException, Request, status
from app.errors import RepositoryError, ValidationError

from app.model.family import FamilyCreateDTO, FamilyReadDTO, FamilyWriteDTO
import app.service.family as family_service

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
    _LOGGER.info(">>> ---------------------------")
    try:
        family = await family_service.get(import_id)
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
    _LOGGER.info("<<< ---------------------------")

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
async def search_family(q: str = "") -> list[FamilyReadDTO]:
    """
    Searches for families matching the "q" URL parameter.

    :param str q: The string to match, defaults to ""
    :raises HTTPException: If nothing found a 404 is returned.
    :return list[FamilyDTO]: A list of matching families.
    """
    families = family_service.search(q)
    if len(families) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Families not found for term: {q}",
        )

    return families


@r.put(
    "/families/{import_id}",
    response_model=FamilyReadDTO,
)
async def update_family(
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
        family = family_service.update(import_id, new_family)
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
