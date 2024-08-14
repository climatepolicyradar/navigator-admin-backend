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
    collection_template = collection_schema["properties"]

    return collection_template


def get_family_event_template():
    event_schema = EventCreateDTO.model_json_schema(mode="serialization")
    event_template = event_schema["properties"]

    del event_template["family_import_id"]
    del event_template["family_document_import_id"]
    _LOGGER.info(json.dumps(event_template, indent=4))

    return event_template


def get_document_template():
    document_schema = DocumentCreateDTO.model_json_schema(mode="serialization")
    document_template = document_schema["properties"]

    del document_template["family_import_id"]
    document_template["events"] = ""

    return document_template


def get_family_metadata_template(corpus_type: str):
    # hardcoding UNFCC taxonomy for the moment
    # will need to look up valid_metadata in the corpus_type table where name == corpus_type
    return {
        "author": {
            "allow_any": "false",
            "allow_blanks": "false",
            "allowed_values": ["Author One", "Author Two"],
        },
        "author_type": {
            "allow_any": "false",
            "allow_blanks": "false",
            "allowed_values": ["Type One", "Type Two"],
        },
        "event_type": {
            "allow_any": "false",
            "allow_blanks": "false",
            "allowed_values": ["Event One", "Event Two"],
        },
        "_document": {
            "role": {
                "allow_any": "false",
                "allow_blanks": "false",
                "allowed_values": ["Role One", "Role Two"],
            },
            "type": {
                "allow_any": "false",
                "allow_blanks": "false",
                "allowed_values": ["Type One", "Type Two"],
            },
        },
    }


def get_family_template(corpus_type: str):
    family_schema = FamilyCreateDTO.model_json_schema(mode="serialization")
    family_template = family_schema["properties"]

    # temp delete
    del family_template["corpus_import_id"]

    # look up taxonomy by corpus type
    family_metadata = get_family_metadata_template(corpus_type)
    # pull out document taxonomy
    document_metadata = family_metadata.pop("_document")

    # add family metadata and event templates to the family template
    family_template["metadata"] = family_metadata
    family_template["events"] = [get_family_event_template()]

    # get document template
    document_template = get_document_template()
    # add document metadata template
    document_template["metadata"] = document_metadata
    # add document template to the family template
    family_template["documents"] = [document_template]
    # _LOGGER.info(json.dumps(family_template, indent=4))
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
