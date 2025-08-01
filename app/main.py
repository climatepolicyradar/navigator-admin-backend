"""
Main configuration for our FastAPI application routes for the admin service.

Note: If you want to add a new endpoint, please make sure you update
AuthEndpoint and the AUTH_TABLE in app/clients/db/models/app/authorisation.py.
"""

import logging
from contextlib import asynccontextmanager

import uvicorn
from db_client import run_migrations
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_health import health
from fastapi_pagination import add_pagination
from fastapi_utils.timing import add_timing_middleware

from app.api.api_v1.routers import (
    analytics_router,
    app_token_router,
    auth_router,
    bulk_import_router,
    collections_router,
    config_router,
    corpora_router,
    corpus_types_router,
    document_router,
    event_router,
    families_router,
    organisations_router,
)
from app.api.api_v1.routers.auth import check_user_auth
from app.clients.db.session import engine
from app.logging_config import DEFAULT_LOGGING, setup_json_logging
from app.service.health import is_database_online

_ALLOW_ORIGIN_REGEX = (
    r"http://localhost:3000|"
    r"https://.+\.climatepolicyradar\.org|"
    r"https://.+\.staging.climatepolicyradar\.org|"
    r"https://.+\.sandbox\.climatepolicyradar\.org|"
    r"https://climate-laws\.org|"
    r"https://.+\.climate-laws\.org|"
)

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)


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
add_timing_middleware(app, record=_LOGGER.info, exclude="health")

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
    bulk_import_router,
    prefix="/api/v1",
    tags=["bulk-import"],
    dependencies=[Depends(check_user_auth)],
)

app.include_router(auth_router, prefix="/api", tags=["Authentication"])

app.include_router(
    corpora_router,
    prefix="/api/v1",
    tags=["corpora"],
    dependencies=[Depends(check_user_auth)],
)

app.include_router(
    corpus_types_router,
    prefix="/api/v1",
    tags=["corpus-types"],
    dependencies=[Depends(check_user_auth)],
)

app.include_router(
    organisations_router,
    prefix="/api/v1",
    tags=["organisations"],
    dependencies=[Depends(check_user_auth)],
)

app.include_router(
    app_token_router,
    prefix="/api/v1",
    tags=["app-token"],
    dependencies=[Depends(check_user_auth)],
)

# Add CORS middleware to allow cross origin requests from any port.
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
