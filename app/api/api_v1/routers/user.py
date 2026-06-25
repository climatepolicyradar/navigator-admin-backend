import logging

from fastapi import APIRouter, HTTPException, status

from app.errors import RepositoryError, ValidationError
from app.model.user import UserReadDTO, UserWriteDTO
from app.service import app_user as user_service
from app.telemetry_exceptions import ExceptionHandlingTelemetryRoute

user_router = APIRouter(route_class=ExceptionHandlingTelemetryRoute)

_LOGGER = logging.getLogger(__name__)


@user_router.get("/users", response_model=list[UserReadDTO])
async def get_all_users() -> list[UserReadDTO]:
    """Return all users with their organisation memberships."""
    try:
        return user_service.all_users()
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )


@user_router.get("/users/{email}", response_model=UserReadDTO)
async def get_user(email: str) -> UserReadDTO:
    """Return a single user by email."""
    try:
        user = user_service.get_user(email)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {email}",
        )
    return user


@user_router.put("/users/{email}", response_model=UserReadDTO)
async def update_user(email: str, user_write: UserWriteDTO) -> UserReadDTO:
    """Update a user's name and organisation memberships.

    Replaces the user's org memberships with the supplied list.
    Superuser only.
    """
    try:
        updated = user_service.update_user(email, user_write)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {email}",
        )
    return updated
