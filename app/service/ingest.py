"""
Ingest Service

This layer uses the corpus, collection, family, document and event repos to handle bulk 
import of data and other services for validation etc.
"""

import logging
from enum import Enum
from typing import Any, Optional, Type, TypeVar
from uuid import uuid4

from db_client.models.dfce.collection import Collection
from db_client.models.dfce.family import Family, FamilyDocument, FamilyEvent
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
import app.service.validation as validation
from app.clients.aws.s3bucket import upload_ingest_json_to_s3
from app.model.ingest import (
    IngestCollectionDTO,
    IngestDocumentDTO,
    IngestEventDTO,
    IngestFamilyDTO,
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
    total_documents_saved = 0

    for doc in document_data:
        if (
            not _exists_in_db(FamilyDocument, doc["import_id"], db)
            and total_documents_saved < DOCUMENT_INGEST_LIMIT
        ):
            _LOGGER.info(f"Importing document {doc['import_id']}")
            dto = IngestDocumentDTO(**doc).to_document_create_dto()
            import_id = document_repository.create(db, dto)
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

    event_import_ids = []
    total_events_saved = 0

    for event in event_data:
        if not _exists_in_db(FamilyEvent, event["import_id"], db):
            _LOGGER.info(f"Importing event {event['import_id']}")
            dto = IngestEventDTO(**event).to_event_create_dto()
            import_id = event_repository.create(db, dto)
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
    ingest_uuid = uuid4()
    upload_ingest_json_to_s3(f"{ingest_uuid}-request", corpus_import_id, data)

    _LOGGER.info("Getting DB session")

    db = db_session.get_db()

    collection_data = data["collections"] if "collections" in data else None
    family_data = data["families"] if "families" in data else None
    document_data = data["documents"] if "documents" in data else None
    event_data = data["events"] if "events" in data else None

    response = {}

    try:
        if collection_data:
            _LOGGER.info("Saving collections")
            response["collections"] = save_collections(
                collection_data, corpus_import_id, db
            )
        if family_data:
            _LOGGER.info("Saving families")
            response["families"] = save_families(family_data, corpus_import_id, db)
        if document_data:
            _LOGGER.info("Saving documents")
            response["documents"] = save_documents(document_data, corpus_import_id, db)
        if event_data:
            _LOGGER.info("Saving events")
            response["events"] = save_events(event_data, corpus_import_id, db)

        _LOGGER.info(
            f"Bulk import for corpus: {corpus_import_id} successfully completed"
        )

        upload_ingest_json_to_s3(f"{ingest_uuid}-result", corpus_import_id, response)

    except Exception as e:
        _LOGGER.error(
            f"Rolling back transaction due to the following error: {e}", exc_info=True
        )
        db.rollback()
    finally:
        db.commit()
