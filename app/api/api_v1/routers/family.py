from fastapi import APIRouter, HTTPException

from app.model.family import FamilyResponse
import app.repository.family as family_repo

families_router = r = APIRouter()


@r.get(
    "/families/{import_id}",
    response_model=FamilyResponse,
)
async def get_family(
    import_id: str,
):
    family = family_repo.get_family(import_id)
    if family is None:
        raise HTTPException(status_code=404, detail=f"Family not found: {import_id}")

    return family
