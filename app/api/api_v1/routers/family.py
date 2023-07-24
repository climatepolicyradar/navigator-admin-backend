"""
Endpoints for managing the Family entity.

It was considered to create a "service" layer that would use the repo 
directly.  However, this API has little / no logic in so the service 
layer would just pass through directly to the repo. So the approach
implemented directly accesses the "repository" layer.
"""
from fastapi import APIRouter, HTTPException

from app.model.family import FamilyDTO
import app.repository.family as family_repo

families_router = r = APIRouter()


@r.get(
    "/families/{import_id}",
    response_model=FamilyDTO,
)
async def get_family(
    import_id: str,
) -> FamilyDTO:
    """
    Returns a specific family given the import id.

    :param str import_id: Specified import_id.
    :raises HTTPException: If the family is not found a 404 is returned.
    :return FamilyDTO: returns a FamilyDTO of the family found.
    """
    family = family_repo.get_family(import_id)
    if family is None:
        raise HTTPException(status_code=404, detail=f"Family not found: {import_id}")

    return family


@r.get(
    "/families/",
    response_model=list[FamilyDTO],
)
async def search_family(q: str = "") -> list[FamilyDTO]:
    """
    Searches for families matching the "q" URL parameter.

    :param str q: The string to match, defaults to ""
    :raises HTTPException: If nothing found a 404 is returned.
    :return list[FamilyDTO]: A list of matching families.
    """
    families = family_repo.search_families(q)
    if families is None or len(families) == 0:
        raise HTTPException(status_code=404, detail=f"Families not found for term: {q}")

    return families


@r.put(
    "/families/{import_id}",
    response_model=FamilyDTO,
)
async def update_family(
    import_id: str,
    new_family: FamilyDTO,
) -> FamilyDTO:
    """
    Updates a specific family given the import id.

    :param str import_id: Specified import_id.
    :raises HTTPException: If the family is not found a 404 is returned.
    :return FamilyDTO: returns a FamilyDTO of the family updated.
    """
    family = family_repo.update_family(import_id, new_family)
    if family is None:
        raise HTTPException(status_code=404, detail=f"Family not updated: {import_id}")

    # TODO: Handle db errors when implemented

    return family


@r.post(
    "/families",
    response_model=FamilyDTO,
)
async def create_family(
    new_family: FamilyDTO,
) -> FamilyDTO:
    """
    Creates a specific family given the import id.

    :raises HTTPException: If the family is not found a 404 is returned.
    :return FamilyDTO: returns a FamilyDTO of the new family.
    """
    family = family_repo.create_family(new_family)
    if family is None:
        raise HTTPException(
            status_code=404, detail=f"Family not created: {new_family.import_id}"
        )

    # TODO: Handle db errors when implemented

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
    family_deleted = family_repo.delete_family(import_id)
    if not family_deleted:
        raise HTTPException(status_code=404, detail=f"Family not deleted: {import_id}")
