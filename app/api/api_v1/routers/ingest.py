import json
import logging

from db_client.models.dfce.taxonomy_entry import EntitySpecificTaxonomyKeys
from db_client.models.organisation.counters import CountedEntity
from fastapi import APIRouter, HTTPException, UploadFile, status

import app.service.taxonomy as taxonomy
from app.errors import RepositoryError, ValidationError
from app.model.general import Json
from app.model.ingest import (
    IngestCollectionDTO,
    IngestDocumentDTO,
    IngestEventDTO,
    IngestFamilyDTO,
)
from app.service.ingest import import_data

ingest_router = r = APIRouter()

_LOGGER = logging.getLogger(__name__)


def _get_collection_template() -> dict:
    """
    Gets a collection template.

    :return dict: The collection template.
    """
    collection_schema = IngestCollectionDTO.model_json_schema(mode="serialization")
    collection_template = collection_schema["properties"]

    return collection_template


def _get_event_template(corpus_type: str) -> dict:
    """
    Gets an event template.

    :return dict: The event template.
    """
    event_schema = IngestEventDTO.model_json_schema(mode="serialization")
    event_template = event_schema["properties"]
    event_template["event_type_value"] = _get_metadata_template(
        corpus_type, CountedEntity.Event
    )

    return event_template


def _get_document_template(corpus_type: str) -> dict:
    """
    Gets a document template for a given corpus type.

    :param str corpus_type: The corpus_type to use to get the document template.
    :return dict: The document template.
    """
    document_schema = IngestDocumentDTO.model_json_schema(mode="serialization")
    document_template = document_schema["properties"]
    document_template["metadata"] = _get_metadata_template(
        corpus_type, CountedEntity.Document
    )

    return document_template


def _get_metadata_template(corpus_type: str, metadata_type: CountedEntity) -> dict:
    """
    Gets a metadata template for a given corpus type and entity.

    :param str corpus_type: The corpus_type to use to get the metadata template.
    :param str metadata_type: The metadata_type to use to get the metadata template.
    :return dict: The metadata template.
    """
    metadata = taxonomy.get(corpus_type)
    if not metadata:
        return {}
    if metadata_type == CountedEntity.Document:
        return metadata.pop(EntitySpecificTaxonomyKeys.DOCUMENT.value)
    elif metadata_type == CountedEntity.Event:
        return metadata.pop(EntitySpecificTaxonomyKeys.EVENT.value)
    elif metadata_type == CountedEntity.Family:
        metadata.pop(EntitySpecificTaxonomyKeys.DOCUMENT.value)
        metadata.pop(EntitySpecificTaxonomyKeys.EVENT.value)
    return metadata


def _get_family_template(corpus_type: str) -> dict:
    """
    Gets a family template for a given corpus type.

    :param str corpus_type: The corpus_type to use to get the family template.
    :return dict: The family template.
    """
    family_schema = IngestFamilyDTO.model_json_schema(mode="serialization")
    family_template = family_schema["properties"]

    del family_template["corpus_import_id"]

    family_metadata = _get_metadata_template(corpus_type, CountedEntity.Family)
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
        "collections": [_get_collection_template()],
        "families": [_get_family_template(corpus_type)],
        "documents": [_get_document_template(corpus_type)],
        "events": [_get_event_template(corpus_type)],
    }


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
    try:
        return import_data(data_dict, corpus_import_id)
    except ValidationError as e:
        _LOGGER.error(e.message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except RepositoryError as e:
        _LOGGER.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )
    except HTTPException as e:
        _LOGGER.error(e)
        raise e
    except Exception as e:
        _LOGGER.error(e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Unexpected error"
        )
