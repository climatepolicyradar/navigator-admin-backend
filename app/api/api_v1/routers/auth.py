import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.errors.authentication_error import AuthenticationError
from app.errors.repository_error import RepositoryError
from app.model.jwt_user import JWTUser
from app.service.authentication import authenticate_user
import app.service.token as token_service

auth_router = r = APIRouter()

_LOGGER = logging.getLogger(__file__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/tokens")


def get_current_user(token: str = Depends(oauth2_scheme)) -> JWTUser:
    return token_service.decode(token)


def enforce_superuser(user: JWTUser) -> None:
    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No authorisation for this operation",
            headers={"WWW-Authenticate": "Bearer"},
        )


@r.post("/tokens")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    _LOGGER.info(
        "Auth token requested",
        extra={"props": {"user_id": form_data.username}},
    )

    try:
        access_token = authenticate_user(form_data.username, form_data.password)
    except (RepositoryError, AuthenticationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    _LOGGER.info(
        "Auth token generated",
        extra={"props": {"user_id": form_data.username}},
    )
    return {"access_token": access_token, "token_type": "bearer"}
