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


def get_family_metadata_template(corpus_type: str):
    # hardcoding UNFCC taxonomy for the moment
    # will need to look up valid_metadata in the corpus_type table where name == corpus_type
    return {
        "author": "",
        "author_type": "",
        "event_type": "",
        "_document": {"type": "", "role": ""},
    }


def get_family_template(corpus_type: str):
    family_schema = FamilyCreateDTO.model_json_schema(mode="serialization")
    family_properties = family_schema["properties"]

    # set all values to empty strings
    family_template = {x: "" for x in family_properties}
    # add organisation to be added manually by user (currently not part of the create family DTO)
    family_template["organisation"] = ""

    # look up taxonomy by corpus type
    family_metadata = get_family_metadata_template(corpus_type)
    # pull out document taxonomy
    document_metadata = family_metadata.pop("_document")

    # add family metadata and event templates to the family template
    family_template["metadata"] = json.dumps(family_metadata)
    family_template["events"] = json.dumps([get_family_event_template()])

    # get document template
    document_template = get_document_template()
    # add document metadata template
    document_template["metadata"] = document_metadata
    # add document template to the family template
    family_template["documents"] = json.dumps([document_template])

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
        "families": [get_family_template(corpus_type)],
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
