from fastapi import APIRouter, HTTPException, Request, status

import app.service.family as family_service
from app.errors import AuthorisationError, RepositoryError, ValidationError

ingest_router = r = APIRouter()


@r.post("/ingest", response_model=str, status_code=status.HTTP_201_CREATED)
async def ingest_data(request: Request, new_data: str) -> str:
    """
    Creates a specific family given the import id.

    :param Request request: Request object.
    :param FamilyCreateDTO new_family: New family data object.
    :raises HTTPException: If the family is not found a 404 is returned.
    :return FamilyDTO: returns a FamilyDTO of the new family.
    """
    try:
        print("HI!!!")
        # family = family_service.create(null, request.state.user)
    except AuthorisationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )

    return ""
