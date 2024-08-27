import json
import logging

from fastapi import APIRouter, HTTPException, UploadFile, status

import app.service.collection as collection
import app.service.corpus as corpus
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

    return event_template


def get_document_template(corpus_type: str):
    document_schema = IngestDocumentDTO.model_json_schema(mode="serialization")
    document_template = document_schema["properties"]
    document_template["metadata"] = get_metadata_template(corpus_type, "document")

    return document_template


def get_metadata_template(corpus_type: str, metadata_type: str):
    metadata = taxonomy.get(corpus_type)
    if not metadata:
        return {}
    if metadata_type == "document":
        return metadata.pop("_document")
    elif metadata_type == "family":
        metadata.pop("_document")
    return metadata


def get_family_template(corpus_type: str):
    family_schema = IngestFamilyDTO.model_json_schema(mode="serialization")
    family_template = family_schema["properties"]

    del family_template["corpus_import_id"]

    family_metadata = get_metadata_template(corpus_type, "family")
    family_template["metadata"] = family_metadata

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
        "documents": [get_document_template(corpus_type)],
        "events": [get_event_template()],
    }


@r.post(
    "/ingest/{corpus_import_id}",
    response_model=Json,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_data(new_data: UploadFile, corpus_import_id: str) -> Json:
    """
    Bulk import endpoint.

    :param UploadFile new_data: file containing json representation of data to ingest.
    :return Json: json representation of the data to ingest.
    """

    content = await new_data.read()
    data_dict = json.loads(content)
    collection_data = data_dict["collections"]

    if not collection_data:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)

    collection_import_ids = []
    try:
        org_id = corpus.get_corpus_org_id(corpus_import_id)
        for item in collection_data:
            dto = IngestCollectionDTO(**item).to_collection_create_dto()
            import_id = collection.create(dto, org_id=org_id)
            collection_import_ids.append(import_id)

        return {"collections": collection_import_ids}
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
