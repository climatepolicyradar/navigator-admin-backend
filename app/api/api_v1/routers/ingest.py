import logging

from fastapi import APIRouter, UploadFile, status

from app.model.collection import CollectionCreateDTO
from app.model.general import Json

ingest_router = r = APIRouter()

_LOGGER = logging.getLogger(__name__)


@r.get(
    "/ingest/template/{corpus_type}",
    response_model=Json,
    status_code=status.HTTP_200_OK,
)
async def get_ingest_template(corpus_type: str) -> Json:
    """
    Data ingest template endpoint.

    :param str corpus_type: type of the corpus of data to ingest.
    :return Json: json representation of ingest template.
    """

    collection_schema = CollectionCreateDTO.model_json_schema(mode="serialization")
    collection_properties = collection_schema["properties"]

    collection_template = {x: "" for x in collection_properties}

    _LOGGER.info(corpus_type)

    return {"collections": [collection_template]}


@r.post("/ingest", response_model=Json, status_code=status.HTTP_201_CREATED)
async def ingest_data(new_data: UploadFile) -> Json:
    """
    Bulk import endpoint.

    :param UploadFile new_data: file containing json representation of data to ingest.
    :return Json: json representation of the data to ingest.
    """
    _LOGGER.info(new_data)
    return {"hello": "world"}
