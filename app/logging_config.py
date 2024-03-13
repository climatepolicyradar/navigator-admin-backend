import logging
import logging.config
import os

import json_logging
from fastapi import FastAPI

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


def setup_json_logging(app: FastAPI):
    json_logging.init_fastapi(enable_json=True)
    json_logging.init_request_instrument(app)
    json_logging.config_root_logger()
