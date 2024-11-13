"""
Ingest Service

This layer uses the corpus, collection, family, document and event repos to handle bulk 
import of data and other services for validation etc.
"""

import logging
from enum import Enum
from typing import Any, Optional, Type, TypeVar

from db_client.models.dfce.collection import Collection
from db_client.models.dfce.family import Family, FamilyDocument, FamilyEvent
from db_client.models.dfce.taxonomy_entry import EntitySpecificTaxonomyKeys
from db_client.models.organisation.counters import CountedEntity
from fastapi import HTTPException, status
from pydantic import ConfigDict, validate_call
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import Session

import app.clients.db.session as db_session
import app.repository.collection as collection_repository
import app.repository.document as document_repository
import app.repository.event as event_repository
import app.repository.family as family_repository
import app.service.corpus as corpus
import app.service.geography as geography
import app.service.notification as notification_service
import app.service.taxonomy as taxonomy
import app.service.validation as validation
from app.errors import ValidationError
from app.model.ingest import (
    IngestCollectionDTO,
    IngestDocumentDTO,
    IngestEventDTO,
    IngestFamilyDTO,
)
from app.repository.helpers import generate_slug
from app.service.event import (
    create_event_metadata_object,
    get_datetime_event_name_for_corpus,
)

DOCUMENT_INGEST_LIMIT = 1000
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)


class IngestEntityList(str, Enum):
    """Name of the list of entities that can be ingested."""

    Collections = "collections"
    Families = "families"
    Documents = "documents"
    Events = "events"


class BaseModel(DeclarativeMeta):
    import_id: str


T = TypeVar("T", bound=BaseModel)


def _exists_in_db(entity: Type[T], import_id: str, db: Session) -> bool:
    """
    Check if a entity exists in the database by import_id.

    :param Type[T] entity: The model of the entity to be looked up in the db.
    :param str import_id: The import_id of the entity.
    :param Session db: The database session.
    :return bool: True if the entity exists, False otherwise.
    """
    entity_exists = db.query(entity).filter(entity.import_id == import_id).one_or_none()
    return entity_exists is not None


def get_collection_template() -> dict:
    """
    Gets a collection template.

    :return dict: The collection template.
    """
    collection_schema = IngestCollectionDTO.model_json_schema(mode="serialization")
    collection_template = collection_schema["properties"]

    return collection_template


def get_event_template(corpus_type: str) -> dict:
    """
    Gets an event template.

    :return dict: The event template.
    """
    event_schema = IngestEventDTO.model_json_schema(mode="serialization")
    event_template = event_schema["properties"]

    event_meta = get_metadata_template(corpus_type, CountedEntity.Event)

    # TODO: Replace with event_template["metadata"] in PDCT-1622
    if "event_type" not in event_meta:
        raise ValidationError("Bad taxonomy in database")
    event_template["event_type_value"] = event_meta["event_type"]

    return event_template


def get_document_template(corpus_type: str) -> dict:
    """
    Gets a document template for a given corpus type.

    :param str corpus_type: The corpus_type to use to get the document template.
    :return dict: The document template.
    """
    document_schema = IngestDocumentDTO.model_json_schema(mode="serialization")
    document_template = document_schema["properties"]
    document_template["metadata"] = get_metadata_template(
        corpus_type, CountedEntity.Document
    )

    return document_template


def get_metadata_template(corpus_type: str, metadata_type: CountedEntity) -> dict:
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
        metadata.pop("event_type")  # TODO: Remove as part of PDCT-1622
    return metadata


def get_family_template(corpus_type: str) -> dict:
    """
    Gets a family template for a given corpus type.

    :param str corpus_type: The corpus_type to use to get the family template.
    :return dict: The family template.
    """
    family_schema = IngestFamilyDTO.model_json_schema(mode="serialization")
    family_template = family_schema["properties"]

    del family_template["corpus_import_id"]

    family_metadata = get_metadata_template(corpus_type, CountedEntity.Family)
    family_template["metadata"] = family_metadata

    return family_template


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def save_collections(
    collection_data: list[dict[str, Any]],
    corpus_import_id: str,
    db: Optional[Session] = None,
) -> list[str]:
    """
    Creates new collections with the values passed.

    :param list[dict[str, Any]] collection_data: The data to use for creating collections.
    :param str corpus_import_id: The import_id of the corpus the collections belong to.
    :param Optional[Session] db: The database session to use for saving collections or None.
    :return list[str]: The new import_ids for the saved collections.
    """
    if db is None:
        db = db_session.get_db()

    validation.validate_collections(collection_data)

    collection_import_ids = []
    org_id = corpus.get_corpus_org_id(corpus_import_id)
    total_collections_saved = 0

    for coll in collection_data:
        if not _exists_in_db(Collection, coll["import_id"], db):
            _LOGGER.info(f"Importing collection {coll['import_id']}")
            dto = IngestCollectionDTO(**coll).to_collection_create_dto()
            import_id = collection_repository.create(db, dto, org_id)
            collection_import_ids.append(import_id)
            total_collections_saved += 1

    _LOGGER.info(f"Saved {total_collections_saved} collections")
    return collection_import_ids


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def save_families(
    family_data: list[dict[str, Any]],
    corpus_import_id: str,
    db: Optional[Session] = None,
) -> list[str]:
    """
    Creates new families with the values passed.

    :param list[dict[str, Any]] family_data: The data to use for creating families.
    :param str corpus_import_id: The import_id of the corpus the families belong to.
    :param Optional[Session] db: The database session to use for saving families or None.
    :return list[str]: The new import_ids for the saved families.
    """

    if db is None:
        db = db_session.get_db()

    validation.validate_families(family_data, corpus_import_id)

    family_import_ids = []
    org_id = corpus.get_corpus_org_id(corpus_import_id)
    total_families_saved = 0

    for fam in family_data:
        if not _exists_in_db(Family, fam["import_id"], db):
            _LOGGER.info(f"Importing family {fam['import_id']}")
            dto = IngestFamilyDTO(
                **fam, corpus_import_id=corpus_import_id
            ).to_family_create_dto(corpus_import_id)
            geo_ids = []
            for geo in dto.geography:
                geo_ids.append(geography.get_id(db, geo))
            import_id = family_repository.create(db, dto, geo_ids, org_id)
            family_import_ids.append(import_id)
            total_families_saved += 1

    _LOGGER.info(f"Saved {total_families_saved} families")

    return family_import_ids


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def save_documents(
    document_data: list[dict[str, Any]],
    corpus_import_id: str,
    db: Optional[Session] = None,
) -> list[str]:
    """
    Creates new documents with the values passed.

    :param list[dict[str, Any]] document_data: The data to use for creating documents.
    :param str corpus_import_id: The import_id of the corpus the documents belong to.
    :param Optional[Session] db: The database session to use for saving documents or None.
    :return list[str]: The new import_ids for the saved documents.
    """
    if db is None:
        db = db_session.get_db()

    validation.validate_documents(document_data, corpus_import_id)

    document_import_ids = []
    document_slugs = set()
    total_documents_saved = 0

    for doc in document_data:
        if (
            not _exists_in_db(FamilyDocument, doc["import_id"], db)
            and total_documents_saved < DOCUMENT_INGEST_LIMIT
        ):
            _LOGGER.info(f"Importing document {doc['import_id']}")
            dto = IngestDocumentDTO(**doc).to_document_create_dto()
            slug = generate_slug(db=db, title=dto.title, created_slugs=document_slugs)
            import_id = document_repository.create(db, dto, slug)
            document_slugs.add(slug)
            document_import_ids.append(import_id)
            total_documents_saved += 1

    _LOGGER.info(f"Saved {total_documents_saved} documents")
    return document_import_ids


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def save_events(
    event_data: list[dict[str, Any]],
    corpus_import_id: str,
    db: Optional[Session] = None,
) -> list[str]:
    """
    Creates new events with the values passed.

    :param list[dict[str, Any]] event_data: The data to use for creating events.
    :param str corpus_import_id: The import_id of the corpus the events belong to.
    :param Optional[Session] db: The database session to use for saving events or None.
    :return list[str]: The new import_ids for the saved events.
    """
    if db is None:
        db = db_session.get_db()

    validation.validate_events(event_data, corpus_import_id)
    datetime_event_name = get_datetime_event_name_for_corpus(db, corpus_import_id)

    event_import_ids = []
    total_events_saved = 0

    for event in event_data:
        if not _exists_in_db(FamilyEvent, event["import_id"], db):
            _LOGGER.info(f"Importing event {event['import_id']}")
            dto = IngestEventDTO(**event).to_event_create_dto()
            event_metadata = create_event_metadata_object(
                db, corpus_import_id, event["event_type_value"], datetime_event_name
            )
            import_id = event_repository.create(db, dto, event_metadata)
            event_import_ids.append(import_id)
            total_events_saved += 1

    _LOGGER.info(f"Saved {total_events_saved} events")
    return event_import_ids


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def import_data(data: dict[str, Any], corpus_import_id: str) -> None:
    """
    Imports data for a given corpus_import_id.

    :param dict[str, Any] data: The data to be imported.
    :param str corpus_import_id: The import_id of the corpus the data should be imported into.
    :raises RepositoryError: raised on a database error.
    :raises ValidationError: raised should the data be invalid.
    """
    notification_service.send_notification(
        f"🚀 Bulk import for corpus: {corpus_import_id} has started."
    )
    end_message = ""

    # ingest_uuid = uuid4()
    # upload_ingest_json_to_s3(f"{ingest_uuid}-request", corpus_import_id, data)

    _LOGGER.info("Getting DB session")

    db = db_session.get_db()

    collection_data = data["collections"] if "collections" in data else None
    family_data = data["families"] if "families" in data else None
    document_data = data["documents"] if "documents" in data else None
    event_data = data["events"] if "events" in data else None

    result = {}

    try:
        if collection_data:
            _LOGGER.info("Saving collections")
            result["collections"] = save_collections(
                collection_data, corpus_import_id, db
            )
        if family_data:
            _LOGGER.info("Saving families")
            result["families"] = save_families(family_data, corpus_import_id, db)
        if document_data:
            _LOGGER.info("Saving documents")
            result["documents"] = save_documents(document_data, corpus_import_id, db)
        if event_data:
            _LOGGER.info("Saving events")
            result["events"] = save_events(event_data, corpus_import_id, db)

        # upload_ingest_json_to_s3(f"{ingest_uuid}-result", corpus_import_id, result)

        end_message = (
            f"🎉 Bulk import for corpus: {corpus_import_id} successfully completed."
        )
        db.commit()
    except Exception as e:
        _LOGGER.error(
            f"Rolling back transaction due to the following error: {e}", exc_info=True
        )
        db.rollback()
        end_message = f"💥 Bulk import for corpus: {corpus_import_id} has failed."
    finally:
        notification_service.send_notification(end_message)


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
