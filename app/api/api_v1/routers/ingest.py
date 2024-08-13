import logging

from fastapi import APIRouter, UploadFile, status

from app.model.general import Json

ingest_router = r = APIRouter()

_LOGGER = logging.getLogger(__name__)


@r.get(
    "/ingest/template/{corpus_id}", response_model=Json, status_code=status.HTTP_200_OK
)
async def get_ingest_template(corpus_id: str) -> Json:
    """
    Data ingest template endpoint.

    :param str corpus_id: id of the corpus of data to ingest.
    :return Json: json representation of ingest template.
    """
    _LOGGER.info(corpus_id)
    return {"hello": "world"}


@r.post("/ingest", response_model=Json, status_code=status.HTTP_201_CREATED)
async def ingest_data(new_data: UploadFile) -> Json:
    """
    Bulk import endpoint.

    :param UploadFile new_data: file containing json representation of data to ingest.
    :return Json: json representation of the data to ingest.
    """
    _LOGGER.info(new_data)
    return {"hello": "world"}
