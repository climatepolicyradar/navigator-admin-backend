from enum import Enum
from typing import Any, Optional

from db_client.models.dfce.taxonomy_entry import EntitySpecificTaxonomyKeys
from fastapi import HTTPException, status

import app.clients.db.session as db_session
import app.service.category as category
import app.service.collection as collection
import app.service.corpus as corpus
import app.service.metadata as metadata
from app.errors import ValidationError
from app.service.collection import validate_import_id
from app.service.event import create_event_metadata_object


class IngestEntityList(str, Enum):
    """Name of the list of entities that can be ingested."""

    Collections = "collections"
    Families = "families"
    Documents = "documents"
    Events = "events"


def validate_collection(collection: dict[str, Any]) -> None:
    """
    Validates a collection.

    :param dict[str, Any] collection: The collection object to be validated.
    :raises ValidationError: raised should the data be invalid.
    """
    validate_import_id(collection["import_id"])


def validate_collections(collections: list[dict[str, Any]]) -> None:
    """
    Validates a list of collections.

    :param list[dict[str, Any]] collections: The list of collection objects to be validated.
    """
    for coll in collections:
        validate_collection(coll)


def validate_family(family: dict[str, Any], corpus_import_id: str) -> None:
    """
    Validates a family.

    :param dict[str, Any] family: The family object to be validated.
    :param str corpus_import_id: The corpus_import_id to be used for validating the family object.
    :raises ValidationError: raised should the data be invalid.
    """
    db = db_session.get_db()

    validate_import_id(family["import_id"])
    corpus.validate(db, corpus_import_id)
    category.validate(family["category"])
    collections = set(family["collections"])
    collection.validate_multiple_ids(collections)
    metadata.validate_metadata(db, corpus_import_id, family["metadata"])


def validate_families(families: list[dict[str, Any]], corpus_import_id: str) -> None:
    """
    Validates a list of families.

    :param list[dict[str, Any]] families: The list of family objects to be validated.
    :param str corpus_import_id: The corpus_import_id to be used for validating the family objects.
    """
    for fam in families:
        validate_family(fam, corpus_import_id)


def validate_document(document: dict[str, Any], corpus_import_id: str) -> None:
    """
    Validates a document.

    :param dict[str, Any] document: The document object to be validated.
    :param str corpus_import_id: The corpus_import_id to be used for validating the document object.
    :raises ValidationError: raised should the data be invalid.
    """
    db = db_session.get_db()

    validate_import_id(document["import_id"])
    validate_import_id(document["family_import_id"])
    print(">>>>>>>>>>>>>>>>", document["variant_name"])
    if document["variant_name"] == "":
        raise ValidationError("Variant name is empty")
    metadata.validate_metadata(
        db,
        corpus_import_id,
        document["metadata"],
        EntitySpecificTaxonomyKeys.DOCUMENT.value,
    )


def validate_documents(documents: list[dict[str, Any]], corpus_import_id: str) -> None:
    """
    Validates a list of documents.

    :param list[dict[str, Any]] documents: The list of document objects to be validated.
    :param str corpus_import_id: The corpus_import_id to be used for validating the document objects.
    """
    for doc in documents:
        validate_document(doc, corpus_import_id)


def validate_event(event: dict[str, Any], corpus_import_id: str) -> None:
    """
    Validates an event.

    :param dict[str, Any] event: The event object to be validated.
    :param str corpus_import_id: The corpus_import_id to be used for
        validating the event object.
    :raises ValidationError: raised should the data be invalid.
    """
    validate_import_id(event["import_id"])
    validate_import_id(event["family_import_id"])

    db = db_session.get_db()
    event_metadata = create_event_metadata_object(
        db, corpus_import_id, event["event_type_value"]
    )
    metadata.validate_metadata(
        db,
        corpus_import_id,
        event_metadata,
        EntitySpecificTaxonomyKeys.EVENT.value,
    )


def validate_events(events: list[dict[str, Any]], corpus_import_id: str) -> None:
    """
    Validates a list of events.

    :param list[dict[str, Any]] events: The list of event objects to be
        validated.
    :param str corpus_import_id: The corpus_import_id to be used for
        validating the event objects.
    """
    for ev in events:
        validate_event(ev, corpus_import_id)


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


def validate_ingest_data(data: dict[str, Any]) -> None:
    """
    Validates data to be ingested.

    :param dict[str, Any] data: The data object to be validated.
    :raises HTTPException: raised if data is empty or None.
    """

    if not data:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)

    validate_entity_relationships(data)
