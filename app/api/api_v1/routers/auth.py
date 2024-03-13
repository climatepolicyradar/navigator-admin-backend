import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

import app.service.authorisation as auth_service
import app.service.token as token_service
from app.errors import (
    AuthenticationError,
    AuthorisationError,
    RepositoryError,
    TokenError,
)
from app.service.authentication import authenticate_user

auth_router = r = APIRouter()

_LOGGER = logging.getLogger(__file__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/tokens")

# TODO: We should use maybe use middleware for this see: PDCT-410


async def check_user_auth(
    request: Request, token: str = Depends(oauth2_scheme)
) -> None:
    """
    Checks the current user (id'd by the token) is authorised for the request.

    :param Request request: The request being made
    :param str token: The token the user supplied, defaults to Depends(oauth2_scheme)
    :raises HTTPException: Raised if the user is not authorised
    """
    try:
        user = token_service.decode(token)
        entity = auth_service.path_to_endpoint(request.scope["path"])
        operation = auth_service.http_method_to_operation(request.scope["method"])
    except TokenError:
        msg = f"Invalid token {token}"
        _LOGGER.exception(msg)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=msg,
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = await request.json() if len(await request.body()) > 0 else False
    _LOGGER.info(
        f"AUDIT: {user.email} is performing {operation} on {entity}",
        extra={
            "props": {
                "request": request.scope["path"],
                "user": user.email,
                "op": operation,
                "entity": entity,
                "payload": payload if payload else "null",
            }
        },
    )

    try:
        auth_service.is_authorised(user, entity, operation)
    except AuthorisationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )

    request.state.user = user


@r.post("/tokens")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    _LOGGER.info(
        "Auth token requested",
        extra={"props": {"user_id": form_data.username}},
    )

    try:
        access_token = authenticate_user(form_data.username, form_data.password)
    except (RepositoryError, AuthenticationError) as e:
        _LOGGER.info(f"Error getting token: {e.message}")
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
