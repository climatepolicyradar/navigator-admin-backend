from enum import Enum
from typing import Any, Optional

from db_client.models.dfce.taxonomy_entry import EntitySpecificTaxonomyKeys
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

import app.clients.db.session as db_session
import app.repository.corpus as corpus_repo
import app.service.category as category
import app.service.collection as collection
import app.service.corpus as corpus
import app.service.metadata as metadata
from app.errors import ValidationError
from app.service.collection import validate_import_id


class BulkImportEntityList(str, Enum):
    """Name of the list of entities that can be imported."""

    Collections = "collections"
    Families = "families"
    Documents = "documents"
    Events = "events"


def validate_collection(
    db: Session, collection: dict[str, Any], corpus_import_id: str
) -> None:
    """
    Validates a collection.

    :param Session db: The database session to use for validating collections.
    :param dict[str, Any] collection: The collection object to be validated.
    :param str corpus_import_id: The corpus_import_id to be used for validating the collection object.
    :raises ValidationError: raised should the data be invalid.
    """

    validate_import_id(collection["import_id"])
    metadata_value = collection.get("metadata")
    if metadata_value and metadata_value != {}:
        metadata.validate_metadata(
            db,
            corpus_import_id,
            collection["metadata"],
            EntitySpecificTaxonomyKeys.COLLECTION.value,
        )


def validate_collections(
    collections: list[dict[str, Any]], corpus_import_id: str
) -> None:
    """
    Validates a list of collections.

    :param list[dict[str, Any]] collections: The list of collection objects to be validated.
    :param str corpus_import_id: The corpus_import_id to be used for validating the collection objects.
    """
    with db_session.get_db() as db:
        for coll in collections:
            validate_collection(db, coll, corpus_import_id)


def validate_family(db: Session, family: dict[str, Any], corpus_import_id: str) -> None:
    """
    Validates a family.

    :param Session db: The database session to use for validating families.
    :param dict[str, Any] family: The family object to be validated.
    :param str corpus_import_id: The corpus_import_id to be used for validating the family object.
    :raises ValidationError: raised should the data be invalid.
    """
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
    with db_session.get_db() as db:
        for fam in families:
            validate_family(db, fam, corpus_import_id)


def validate_document(
    db: Session, document: dict[str, Any], corpus_import_id: str
) -> None:
    """
    Validates a document.

    :param Session db: The database session to use for validating documents.
    :param dict[str, Any] document: The document object to be validated.
    :param str corpus_import_id: The corpus_import_id to be used for validating the document object.
    :raises ValidationError: raised should the data be invalid.
    """
    validate_import_id(document["import_id"])
    validate_import_id(document["family_import_id"])
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
    with db_session.get_db() as db:
        for doc in documents:
            validate_document(db, doc, corpus_import_id)


def validate_event(db: Session, event: dict[str, Any], corpus_import_id: str) -> None:
    """
    Validates an event.

    :param Session db: The database session to use for validating events.
    :param dict[str, Any] event: The event object to be validated.
    :param str corpus_import_id: The corpus_import_id to be used for
        validating the event object.
    :raises ValidationError: raised should the data be invalid.
    """
    validate_import_id(event["import_id"])
    validate_import_id(event["family_import_id"])

    event_metadata = event.get("metadata", {})

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
    with db_session.get_db() as db:
        for ev in events:
            validate_event(db, ev, corpus_import_id)


def _collect_import_ids(
    entity_list_name: BulkImportEntityList,
    data: dict[str, Any],
    import_id_type_name: Optional[str] = None,
) -> list[str]:
    """
    Extracts a list of import_ids (or family_import_ids if specified) for the specified entity list in data.

    :param BulkImportEntityList entity_list_name: The name of the entity list from which the import_ids are to be extracted.
    :param dict[str, Any] data: The data structure containing the entity lists used for extraction.
    :param Optional[str] import_id_type_name: the name of the type of import_id to be extracted or None.
    :return list[str]: A list of extracted import_ids for the specified entity list.
    """
    import_id_key = import_id_type_name or "import_id"
    import_ids = []
    if entity_list_name.value in data:
        for entity in data[entity_list_name.value]:
            import_ids.append(entity.get(import_id_key))
    return import_ids


def _match_import_ids(
    parent_references: list[str], parent_import_ids: set[str]
) -> list[str]:
    """
    Validates that all the references to parent entities exist in the set of parent import_ids passed in

    :param list[str] parent_references: List of import_ids referencing parent entities to be validated.
    :param set[str] parent_import_ids: Set of parent import_ids to validate against.
    :returns list[str]: List of parent_references that are referenced in parent_import_ids but are missing from the parent_references
    or an empty list.
    """
    unmatched_import_ids = []
    for id in parent_references:
        if id and id not in parent_import_ids:
            unmatched_import_ids.append(id)

    return unmatched_import_ids


def _validate_collections_exist_for_families(data: dict[str, Any]) -> list[str]:
    """
    Validates that collections the families are linked to exist based on import_id links in data.

    :param dict[str, Any] data: The data object containing entities to be validated.
    :returns list[str]: List of collection ids that are referenced by families but are missing from the list of collections
    or an empty list.
    """
    collections = _collect_import_ids(BulkImportEntityList.Collections, data)
    collections_set = set(collections)

    family_collection_import_ids = []
    if "families" in data:
        for fam in data["families"]:
            family_collection_import_ids.extend(fam["collections"])

    return _match_import_ids(family_collection_import_ids, collections_set)


def _validate_families_exist_for_documents(data: dict[str, Any]) -> list[str]:
    """
    Validates that families, the documents are linked to, exist based on import_id links in data.

    :param dict[str, Any] data: The data object containing entities to be validated.
    :returns list[str]: List of families ids that are referenced by documents but are missing from the list of families
    or an empty list.
    """
    families = _collect_import_ids(BulkImportEntityList.Families, data)
    families_set = set(families)

    document_family_import_ids = _collect_import_ids(
        BulkImportEntityList.Documents, data, "family_import_id"
    )

    return _match_import_ids(document_family_import_ids, families_set)


def _validate_families_exist_for_events(data: dict[str, Any]) -> list[str]:
    """
    Validates that families, the events are linked to, exist based on import_id links in data.

    :param dict[str, Any] data: The data object containing entities to be validated.
    :returns list[str]: List of family ids that are referenced by events but are missing from the list of events
    or an empty list.
    """
    families = _collect_import_ids(BulkImportEntityList.Families, data)
    families_set = set(families)

    event_family_import_ids = _collect_import_ids(
        BulkImportEntityList.Events, data, "family_import_id"
    )

    return _match_import_ids(event_family_import_ids, families_set)


def _validate_documents_exist_for_events(data: dict[str, Any]) -> list[str]:
    """
    Validates that documents, the events are linked to, exist based on import_id links in data.
    Ignores events where document id is None as not all events will be associated with a document.

    :param dict[str, Any] data: The data object containing entities to be validated.
    :returns list[str]: List of document ids that are referenced by events but are missing from the list of events
    or an empty list.
    """
    documents = _collect_import_ids(BulkImportEntityList.Documents, data)
    documents_set = set(documents)

    event_document_import_ids = _collect_import_ids(
        BulkImportEntityList.Events, data, "family_document_import_id"
    )

    return _match_import_ids(event_document_import_ids, documents_set)


def validate_entity_relationships(data: dict[str, Any]) -> None:
    """
    Validates relationships between entities contained in data.
    For documents, it validates that the family the document is linked to exists.

    :param dict[str, Any] data: The data object containing entities to be validated.
    """
    missing_entity_ids = set()
    missing_entity_ids.update(_validate_collections_exist_for_families(data))
    missing_entity_ids.update(_validate_families_exist_for_documents(data))
    missing_entity_ids.update(_validate_families_exist_for_events(data))
    missing_entity_ids.update(_validate_documents_exist_for_events(data))

    if missing_entity_ids:
        missing_entity_ids = sorted(list(missing_entity_ids))
        raise ValidationError(f"Missing entities: {missing_entity_ids}")


def validate_bulk_import_data(data: dict[str, Any]) -> None:
    """
    Validates data to be bulk imported.

    :param dict[str, Any] data: The data object to be validated.
    :raises HTTPException: raised if data is empty or None.
    """

    if not data:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)

    validate_entity_relationships(data)


def validate_corpus_exists(corpus_import_id: str) -> None:
    """
    Validates whether a corpus exists in the db for the given corpus import_id.

    :param str corpus_import_id: The import_id used to find a corpus in the database.
    :raises ValidationError: raised if corpus is not found for the given import_id.
    """
    with db_session.get_db() as db:
        corpus = corpus_repo.get(db, corpus_import_id)

        if corpus is None:
            msg = f"No corpus found for import_id: {corpus_import_id}"
            raise ValidationError(msg)
