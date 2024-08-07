import logging
from typing import Any

from fastapi import APIRouter, status

ingest_router = r = APIRouter()

_LOGGER = logging.getLogger(__name__)


@r.post("/ingest", response_model=dict[str, Any], status_code=status.HTTP_201_CREATED)
async def ingest_data(new_data: dict[str, Any]) -> dict[str, Any]:
    """
    Bulk import endpoint.

    :param dict[str, Any] new_data: json representation of data to ingest.
    :return dict[str, Any]: json representation of the data to ingest.
    """

    _LOGGER.info(new_data)
    return new_data
