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
    family_metadata.pop("_document") if family_metadata else {}

    # add family metadata and event templates to the family template
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
        "documents": [get_document_template()],
        "events": [get_event_template()],
    }


def ingest_data(data: dict, corpus_import_id: str):
    collection_data = data["collections"] if "collections" in data else None
    family_data = data["families"] if "families" in data else None

    if not data:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)

    collection_import_ids = []
    family_import_ids = []
    response = {}
    try:
        org_id = corpus.get_corpus_org_id(corpus_import_id)
        if collection_data:
            for coll in collection_data:
                dto = IngestCollectionDTO(**coll).to_collection_create_dto()
                import_id = collection.create(dto, org_id)
                collection_import_ids.append(import_id)
                response["collections"] = collection_import_ids
        if family_data:
            for fam in family_data:
                dto = IngestFamilyDTO(
                    **fam, corpus_import_id=corpus_import_id
                ).to_family_create_dto(corpus_import_id)
                # import_id = family.create(dto, org_id)
                family_import_ids.append("created")
                response["families"] = family_import_ids

        return response
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@r.post(
    "/ingest/{corpus_import_id}",
    response_model=Json,
    status_code=status.HTTP_201_CREATED,
)
async def ingest(new_data: UploadFile, corpus_import_id: str) -> Json:
    """
    Bulk import endpoint.

    :param UploadFile new_data: file containing json representation of data to ingest.
    :return Json: json representation of the data to ingest.
    """

    content = await new_data.read()
    data_dict = json.loads(content)

    return ingest_data(data_dict, corpus_import_id)
