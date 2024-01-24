import logging

from fastapi import APIRouter, HTTPException, Request, status
from app.model.config import ConfigReadDTO
import app.service.config as config_service
from navigator_db_client.errors import RepositoryError

config_router = r = APIRouter()

_LOGGER = logging.getLogger(__file__)


@r.get("/config", response_model=ConfigReadDTO)
async def get_config(request: Request) -> ConfigReadDTO:
    user = request.state.user
    _LOGGER.info(f"User {user.email} is getting config")
    try:
        config = config_service.get()
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )
    return config
