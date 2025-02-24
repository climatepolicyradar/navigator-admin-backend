import logging

from fastapi import APIRouter, HTTPException, status

from app.errors import AuthorisationError, ValidationError
from app.model.app_token import AppTokenCreateDTO
from app.service.app_token import create_configuration_token

app_token_router = r = APIRouter()

_LOGGER = logging.getLogger(__file__)


@r.post("app-tokens", response_model=str)
async def create_app_token(new_token: AppTokenCreateDTO) -> str:
    """Create a custom app token for the navigator app.

    :param AppTokenCreateDTO new_token: New custom app object.
    :raises HTTPException: If there is an error raised during validation
    :return str: returns the newly encoded custom app token.
    """
    try:
        token = create_configuration_token(new_token)
    except AuthorisationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)

    return token
