from fastapi import APIRouter, HTTPException, Request, status

import app.service.config as config_service
from app.errors import RepositoryError
from app.model.config import ConfigReadDTO
from app.telemetry_exceptions import ExceptionHandlingTelemetryRoute

config_router = r = APIRouter(route_class=ExceptionHandlingTelemetryRoute)


@r.get("/config", response_model=ConfigReadDTO)
async def get_config(request: Request) -> ConfigReadDTO:
    user = request.state.user
    try:
        config = config_service.get(user)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )
    return config
