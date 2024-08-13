import json
import logging

from fastapi import APIRouter, UploadFile, status

from app.model.collection import CollectionCreateDTO
from app.model.document import DocumentCreateDTO
from app.model.event import EventCreateDTO
from app.model.family import FamilyCreateDTO
from app.model.general import Json

ingest_router = r = APIRouter()

_LOGGER = logging.getLogger(__name__)


def get_collection_template():
    collection_schema = CollectionCreateDTO.model_json_schema(mode="serialization")
    collection_properties = collection_schema["properties"]

    collection_template = {x: "" for x in collection_properties}

    return collection_template


def get_family_event_template():
    event_schema = EventCreateDTO.model_json_schema(mode="serialization")
    event_properties = event_schema["properties"]

    del event_properties["family_import_id"]
    del event_properties["family_document_import_id"]
    event_template = {x: "" for x in event_properties}

    return event_template


def get_document_template():
    document_schema = DocumentCreateDTO.model_json_schema(mode="serialization")
    document_properties = document_schema["properties"]

    del document_properties["family_import_id"]
    document_template = {x: "" for x in document_properties}

    return document_template


def get_family_template():
    family_schema = FamilyCreateDTO.model_json_schema(mode="serialization")
    family_properties = family_schema["properties"]

    family_template = {x: "" for x in family_properties}
    family_template["organisation"] = ""
    family_template["events"] = json.dumps([get_family_event_template()])
    family_template["documents"] = json.dumps([get_document_template()])

    return family_template


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

    _LOGGER.info(corpus_type)

    return {
        "collections": [get_collection_template()],
        "families": [get_family_template()],
    }


@r.post("/ingest", response_model=Json, status_code=status.HTTP_201_CREATED)
async def ingest_data(new_data: UploadFile) -> Json:
    """
    Bulk import endpoint.

    :param UploadFile new_data: file containing json representation of data to ingest.
    :return Json: json representation of the data to ingest.
    """
    _LOGGER.info(new_data)
    return {"hello": "world"}
