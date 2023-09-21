import logging

from fastapi import APIRouter, HTTPException, Request, status
import app.service.config as config_service
from app.errors import RepositoryError

config_router = r = APIRouter()

_LOGGER = logging.getLogger(__file__)


@r.get("/config")
async def get_config(request: Request):
    user = request.state.user
    _LOGGER.info(f"User {user.email} is getting config")
    try:
        config = config_service.get()
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Config not found"
        )

    return config
