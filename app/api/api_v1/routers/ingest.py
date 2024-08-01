import logging

from fastapi import APIRouter, Request, status

from app.model.ingest import IngestDTO

ingest_router = r = APIRouter()

_LOGGER = logging.getLogger(__name__)


@r.post("/ingest", response_model=str, status_code=status.HTTP_201_CREATED)
async def ingest_data(new_data: IngestDTO) -> str:
    """
    Bulk import endpoint.

    :param IngestDTO new_data: json representation of data to ingest.
    :return str: corpus_id of the data to ingest into.
    """

    _LOGGER.info(new_data)
    return new_data.corpus_id
