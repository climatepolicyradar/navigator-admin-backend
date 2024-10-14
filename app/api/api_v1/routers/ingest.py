import json
import logging
from enum import Enum
from typing import Any, Optional

from db_client.models.dfce.taxonomy_entry import EntitySpecificTaxonomyKeys
from db_client.models.organisation.counters import CountedEntity
from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, status

import app.service.taxonomy as taxonomy
from app.errors import ValidationError
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


class IngestEntityList(str, Enum):
    """Name of the list of entities that can be ingested."""

    Collections = "collections"
    Families = "families"
    Documents = "documents"
    Events = "events"


def _collect_import_ids(
    entity_list_name: IngestEntityList,
    data: dict[str, Any],
    import_id_type_name: Optional[str] = None,
) -> list[str]:
    """
    Extracts a list of import_ids (or family_import_ids if specified) for the specified entity list in data.

    :param IngestEntityList entity_list_name: The name of the entity list from which the import_ids are to be extracted.
    :param dict[str, Any] data: The data structure containing the entity lists used for extraction.
    :param Optional[str] import_id_type_name: the name of the type of import_id to be extracted or None.
    :return list[str]: A list of extracted import_ids for the specified entity list.
    """
    import_id_key = import_id_type_name or "import_id"
    import_ids = []
    if entity_list_name.value in data:
        for entity in data[entity_list_name.value]:
            import_ids.append(entity[import_id_key])
    return import_ids


def _match_import_ids(
    parent_references: list[str], parent_import_ids: set[str]
) -> None:
    """
    Validates that all the references to parent entities exist in the set of parent import_ids passed in

    :param list[str] parent_references: List of import_ids referencing parent entities to be validated.
    :param set[str] parent_import_ids: Set of parent import_ids to validate against.
    :raises ValidationError: raised if a parent reference is not found in the parent_import_ids.
    """
    for id in parent_references:
        if id not in parent_import_ids:
            raise ValidationError(f"No entity with id {id} found")


def _validate_collections_exist_for_families(data: dict[str, Any]) -> None:
    """
    Validates that collections the families are linked to exist based on import_id links in data.

    :param dict[str, Any] data: The data object containing entities to be validated.
    """
    collections = _collect_import_ids(IngestEntityList.Collections, data)
    collections_set = set(collections)

    family_collection_import_ids = []
    if "families" in data:
        for fam in data["families"]:
            family_collection_import_ids.extend(fam["collections"])

    _match_import_ids(family_collection_import_ids, collections_set)


def _validate_families_exist_for_events_and_documents(data: dict[str, Any]) -> None:
    """
    Validates that families the documents and events are linked to exist
    based on import_id links in data.

    :param dict[str, Any] data: The data object containing entities to be validated.
    """
    families = _collect_import_ids(IngestEntityList.Families, data)
    families_set = set(families)

    document_family_import_ids = _collect_import_ids(
        IngestEntityList.Documents, data, "family_import_id"
    )
    event_family_import_ids = _collect_import_ids(
        IngestEntityList.Events, data, "family_import_id"
    )

    _match_import_ids(document_family_import_ids, families_set)
    _match_import_ids(event_family_import_ids, families_set)


def validate_entity_relationships(data: dict[str, Any]) -> None:
    """
    Validates relationships between entities contained in data.
    For documents, it validates that the family the document is linked to exists.

    :param dict[str, Any] data: The data object containing entities to be validated.
    """

    _validate_collections_exist_for_families(data)
    _validate_families_exist_for_events_and_documents(data)


def _validate_ingest_data(data: dict[str, Any]) -> None:
    """
    Validates data to be ingested.

    :param dict[str, Any] data: The data object to be validated.
    :raises HTTPException: raised if data is empty or None.
    """

    if not data:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)

    validate_entity_relationships(data)


@r.post(
    "/ingest/{corpus_import_id}",
    response_model=Json,
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingest(
    new_data: UploadFile, corpus_import_id: str, background_tasks: BackgroundTasks
) -> Json:
    """
    Bulk import endpoint.

    :param UploadFile new_data: file containing json representation of data to ingest.
    :return Json: json representation of the data to ingest.
    """
    _LOGGER.info(f"Received bulk import request for corpus: {corpus_import_id}")

    try:
        content = await new_data.read()
        data_dict = json.loads(content)
        _validate_ingest_data(data_dict)

        background_tasks.add_task(import_data, data_dict, corpus_import_id)

        return {
            "message": "Bulk import request accepted. Check Cloudwatch logs for result."
        }
    except ValidationError as e:
        _LOGGER.error(e.message, exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except HTTPException as e:
        _LOGGER.error(e, exc_info=True)
        raise e
    except Exception as e:
        _LOGGER.error(e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )
