"""
Ingest Service

This layer uses the corpus, collection, family, document and event repos to handle bulk 
import of data and other services for validation etc.
"""

from enum import Enum
from typing import Any, Optional

from db_client.models.dfce.family import Family, FamilyDocument
from fastapi import HTTPException, status
from pydantic import ConfigDict, validate_call
from sqlalchemy.orm import Session

import app.clients.db.session as db_session
import app.repository.collection as collection_repository
import app.repository.document as document_repository
import app.repository.event as event_repository
import app.repository.family as family_repository
import app.service.corpus as corpus
import app.service.geography as geography
import app.service.validation as validation
from app.errors import ValidationError
from app.model.ingest import (
    IngestCollectionDTO,
    IngestDocumentDTO,
    IngestEventDTO,
    IngestFamilyDTO,
)

DOCUMENT_INGEST_LIMIT = 1000


class IngestEntityList(str, Enum):
    """Name of the list of entities that can be ingested."""

    Collections = "collections"
    Families = "families"
    Documents = "documents"
    Events = "events"


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

    for coll in collection_data:
        dto = IngestCollectionDTO(**coll).to_collection_create_dto()
        import_id = collection_repository.create(db, dto, org_id)
        collection_import_ids.append(import_id)

    return collection_import_ids


def _family_exists_in_db(db: Session, import_id: str) -> bool:
    """
    Check if a family exists in the database by import_id.

    :param Session db: The database session.
    :param str import_id: The import_id of the family.
    :return bool: True if the family exists, False otherwise.
    """
    family_exists = db.query(Family).filter(Family.import_id == import_id).one_or_none()
    return family_exists is not None


def _document_exists_in_db(db: Session, import_id: str) -> bool:
    """
    Check if a document exists in the database by import_id.

    :param Session db: The database session.
    :param str import_id: The import_id of the document.
    :return bool: True if the document exists, False otherwise.
    """
    document_exists = (
        db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == import_id)
        .one_or_none()
    )
    return document_exists is not None


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

    for fam in family_data:
        if not _family_exists_in_db(db, fam["import_id"]):
            dto = IngestFamilyDTO(
                **fam, corpus_import_id=corpus_import_id
            ).to_family_create_dto(corpus_import_id)
            geo_ids = []
            for geo in dto.geography:
                geo_ids.append(geography.get_id(db, geo))
            import_id = family_repository.create(db, dto, geo_ids, org_id)
            family_import_ids.append(import_id)

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
    saved_documents_counter = 0

    for doc in document_data:
        if (
            not _document_exists_in_db(db, doc["import_id"])
            and saved_documents_counter < DOCUMENT_INGEST_LIMIT
        ):
            dto = IngestDocumentDTO(**doc).to_document_create_dto()
            import_id = document_repository.create(db, dto)
            document_import_ids.append(import_id)
            saved_documents_counter += 1

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

    event_import_ids = []

    for event in event_data:
        dto = IngestEventDTO(**event).to_event_create_dto()
        import_id = event_repository.create(db, dto)
        event_import_ids.append(import_id)

    return event_import_ids


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


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def import_data(data: dict[str, Any], corpus_import_id: str) -> dict[str, str]:
    """
    Imports data for a given corpus_import_id.

    :param dict[str, Any] data: The data to be imported.
    :param str corpus_import_id: The import_id of the corpus the data should be imported into.
    :raises RepositoryError: raised on a database error.
    :raises ValidationError: raised should the data be invalid.
    :return dict[str, str]: Import ids of the saved entities.
    """
    _validate_ingest_data(data)

    db = db_session.get_db()

    collection_data = data["collections"] if "collections" in data else None
    family_data = data["families"] if "families" in data else None
    document_data = data["documents"] if "documents" in data else None
    event_data = data["events"] if "events" in data else None

    response = {}

    try:
        if collection_data:
            response["collections"] = save_collections(
                collection_data, corpus_import_id, db
            )
        if family_data:
            response["families"] = save_families(family_data, corpus_import_id, db)
        if document_data:
            response["documents"] = save_documents(document_data, corpus_import_id, db)
        if event_data:
            response["events"] = save_events(event_data, corpus_import_id, db)

        return response
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.commit()
