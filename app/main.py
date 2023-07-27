from fastapi_pagination import add_pagination
from app.logging_config import DEFAULT_LOGGING, setup_json_logging
from app.api.api_v1.routers import families_router
from fastapi import FastAPI
from fastapi_health import health
import uvicorn

from app.service.health import is_database_online


app = FastAPI(title="navigator-admin")
setup_json_logging(app)
add_pagination(app)
app.include_router(families_router, prefix="/api/v1", tags=["families"])

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
