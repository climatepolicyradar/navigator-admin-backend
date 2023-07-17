import logging
import logging.config
import os
from fastapi import FastAPI
import uvicorn


app = FastAPI()


LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
DEFAULT_LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",  # Default is stderr
        },
    },
    "loggers": {},
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
}
logger = logging.getLogger(__name__)
logging.config.dictConfig(DEFAULT_LOGGING)


@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8888,
        log_config=DEFAULT_LOGGING,
        workers=10,
    )  # type: ignore
