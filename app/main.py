"""
Main configuration for our FastAPI application routes for the admin service.

Note: If you want to add a new endpoint, please make sure you update
AuthEndpoint and the AUTH_TABLE in app/clients/db/models/app/authorisation.py.
"""

from contextlib import asynccontextmanager

import uvicorn
from db_client import run_migrations
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_health import health
from fastapi_pagination import add_pagination

from app.api.api_v1.routers import (
    analytics_router,
    auth_router,
    collections_router,
    config_router,
    document_router,
    event_router,
    families_router,
    ingest_router,
)
from app.api.api_v1.routers.auth import check_user_auth
from app.clients.db.session import engine
from app.logging_config import DEFAULT_LOGGING, setup_json_logging
from app.service.health import is_database_online

_ALLOW_ORIGIN_REGEX = (
    r"http://localhost:3000|"
    r"https://.+\.climatepolicyradar\.org|"
    r"https://.+\.dev.climatepolicyradar\.org|"
    r"https://.+\.sandbox\.climatepolicyradar\.org|"
    r"https://climate-laws\.org|"
    r"https://.+\.climate-laws\.org|"
)


@asynccontextmanager
async def lifespan(app_: FastAPI):
    """Run startup and shutdown events."""
    run_migrations(engine)
    yield


app = FastAPI(
    title="navigator-admin",
    lifespan=lifespan,
)
setup_json_logging(app)
add_pagination(app)

app.include_router(
    config_router,
    prefix="/api/v1",
    tags=["config"],
    dependencies=[Depends(check_user_auth)],
)

app.include_router(
    families_router,
    prefix="/api/v1",
    tags=["families"],
    dependencies=[Depends(check_user_auth)],
)

app.include_router(
    collections_router,
    prefix="/api/v1",
    tags=["collections"],
    dependencies=[Depends(check_user_auth)],
)

app.include_router(
    document_router,
    prefix="/api/v1",
    tags=["documents"],
    dependencies=[Depends(check_user_auth)],
)

app.include_router(
    analytics_router,
    prefix="/api/v1",
    tags=["analytics"],
    dependencies=[Depends(check_user_auth)],
)

app.include_router(
    event_router,
    prefix="/api/v1",
    tags=["events"],
    dependencies=[Depends(check_user_auth)],
)

app.include_router(
    ingest_router,
    prefix="/api/v1",
    tags=["ingest"],
    dependencies=[Depends(check_user_auth)],
)

app.include_router(auth_router, prefix="/api", tags=["Authentication"])

# Add CORS middleware to allow cross origin requests from any port
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=_ALLOW_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# add health endpoint
app.add_api_route("/health", health([is_database_online]))


@app.get("/api/v1", include_in_schema=False)
async def root():
    return {"message": "CPR Navigator Admin API v1"}


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8888,
        log_config=DEFAULT_LOGGING,
    )  # type: ignore
