import json
import logging

from fastapi import APIRouter, HTTPException, UploadFile, status

import app.service.collection as collection
import app.service.taxonomy as taxonomy
from app.errors import ValidationError
from app.model.general import Json
from app.model.ingest import (
    IngestCollectionDTO,
    IngestDocumentDTO,
    IngestEventDTO,
    IngestFamilyDTO,
)

ingest_router = r = APIRouter()

_LOGGER = logging.getLogger(__name__)


def get_collection_template():
    collection_schema = IngestCollectionDTO.model_json_schema(mode="serialization")
    collection_template = collection_schema["properties"]

    return collection_template


def get_event_template():
    event_schema = IngestEventDTO.model_json_schema(mode="serialization")
    event_template = event_schema["properties"]

    del event_template["family_document_import_id"]
    del event_template["family_import_id"]

    return event_template


def get_document_template():
    document_schema = IngestDocumentDTO.model_json_schema(mode="serialization")
    document_template = document_schema["properties"]

    del document_template["family_import_id"]
    document_template["events"] = [get_event_template()]

    return document_template


def get_metadata_template(corpus_type: str):
    return taxonomy.get(corpus_type)


def get_family_template(corpus_type: str):
    family_schema = IngestFamilyDTO.model_json_schema(mode="serialization")
    family_template = family_schema["properties"]

    del family_template["corpus_import_id"]

    # look up taxonomy by corpus type
    family_metadata = get_metadata_template(corpus_type)
    # pull out document taxonomy
    document_metadata = family_metadata.pop("_document") if family_metadata else {}

    # add family metadata and event templates to the family template
    family_template["metadata"] = family_metadata

    family_template["events"] = [get_event_template()]

    # get document template
    document_template = get_document_template()
    # add document metadata template
    document_template["metadata"] = document_metadata
    # add document template to the family template
    family_template["documents"] = [document_template]

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

    _LOGGER.info(f"Creating template for corpus type: {corpus_type}")

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

    content = await new_data.read()
    data_dict = json.loads(content)
    collection_data = data_dict["collections"]
    collection_import_ids = []

    try:
        for item in collection_data:
            dto = IngestCollectionDTO(**item).to_collection_create_dto()
            import_id = collection.create(dto, org_id=1)
            collection_import_ids.append(import_id)

        return {"collections": collection_import_ids}
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
