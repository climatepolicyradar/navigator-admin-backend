"""
Bulk Import Service

This layer uses the corpus, collection, family, document and event repos to handle bulk 
import of data and other services for validation etc.
"""

import logging
from typing import Any, Optional, Type, TypeVar
from uuid import uuid4

from db_client.models.dfce.collection import Collection
from db_client.models.dfce.family import Family, FamilyDocument, FamilyEvent
from db_client.models.dfce.taxonomy_entry import EntitySpecificTaxonomyKeys
from db_client.models.organisation.counters import CountedEntity
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
from app.clients.aws.s3bucket import upload_bulk_import_json_to_s3
from app.errors import ValidationError
from app.model.bulk_import import (
    BulkImportCollectionDTO,
    BulkImportDocumentDTO,
    BulkImportEventDTO,
    BulkImportFamilyDTO,
    CollectionComparisonDTO,
    FamilyComparisonDTO,
)
from app.repository.helpers import generate_slug
from app.service.event import (
    create_event_metadata_object,
    get_datetime_event_name_for_corpus,
)

# Any increase to this number should first be discussed with the Platform Team
DEFAULT_DOCUMENT_LIMIT = 1000

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)


class BaseModel(DeclarativeMeta):
    import_id: str


T = TypeVar("T", bound=BaseModel)


def _find_entity_in_db(entity: Type[T], import_id: str, db: Session) -> Type[T]:
    """
    Finds the entity from the database by import_id.

    :param Type[T] entity: The model of the entity to be looked up in the db.
    :param str import_id: The import_id of the entity.
    :param Session db: The database session.
    :return Type[T]: The found entity or None.
    """
    return db.query(entity).filter(entity.import_id == import_id).one_or_none()


def get_collection_template() -> dict:
    """
    Gets a collection template.

    :return dict: The collection template.
    """
    collection_schema = BulkImportCollectionDTO.model_json_schema(mode="serialization")
    collection_template = collection_schema["properties"]

    return collection_template


def get_event_template(corpus_type: str) -> dict:
    """
    Gets an event template.

    :return dict: The event template.
    """
    event_schema = BulkImportEventDTO.model_json_schema(mode="serialization")
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
    document_schema = BulkImportDocumentDTO.model_json_schema(mode="serialization")
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
    family_schema = BulkImportFamilyDTO.model_json_schema(mode="serialization")
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
        existing_collection = _find_entity_in_db(Collection, coll["import_id"], db)
        if not existing_collection:
            _LOGGER.info(f"Importing collection {coll['import_id']}")
            create_dto = BulkImportCollectionDTO(**coll).to_collection_create_dto()
            import_id = collection_repository.create(db, create_dto, org_id)
            collection_import_ids.append(import_id)
            total_collections_saved += 1
        else:
            update_dto = BulkImportCollectionDTO(**coll).to_collection_write_dto()
            existing_dto = CollectionComparisonDTO.from_collection(existing_collection)
            if existing_dto.is_different_from(update_dto):
                _LOGGER.info(f"Updating collection {coll['import_id']}")
                import_id = collection_repository.update(
                    db, coll["import_id"], update_dto
                )
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
        existing_family = _find_entity_in_db(Family, fam["import_id"], db)
        if not existing_family:
            _LOGGER.info(f"Importing family {fam['import_id']}")
            create_dto = BulkImportFamilyDTO(
                **fam, corpus_import_id=corpus_import_id
            ).to_family_create_dto(corpus_import_id)
            geo_ids = [geography.get_id(db, geo) for geo in create_dto.geographies]
            import_id = family_repository.create(db, create_dto, geo_ids, org_id)
            family_import_ids.append(import_id)
            total_families_saved += 1
        else:
            update_dto = BulkImportFamilyDTO(
                **fam, corpus_import_id=corpus_import_id
            ).to_family_write_dto()
            existing_dto = FamilyComparisonDTO.from_family(existing_family, db)
            if existing_dto.is_different_from(update_dto):
                _LOGGER.info(f"Updating family {fam['import_id']}")
                geo_ids = [geography.get_id(db, geo) for geo in update_dto.geographies]
                import_id = family_repository.update(
                    db, fam["import_id"], update_dto, geo_ids
                )
                family_import_ids.append(import_id)
                total_families_saved += 1

    _LOGGER.info(f"Saved {total_families_saved} families")

    return family_import_ids


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def save_documents(
    document_data: list[dict[str, Any]],
    corpus_import_id: str,
    document_limit: int,
    db: Optional[Session] = None,
) -> list[str]:
    """
    Creates new documents with the values passed.

    :param list[dict[str, Any]] document_data: The data to use for creating documents.
    :param str corpus_import_id: The import_id of the corpus the documents belong to.
    :param int document_limit: The max number of documents to be saved in this session.
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
        if total_documents_saved < document_limit:
            if not _find_entity_in_db(FamilyDocument, doc["import_id"], db):
                _LOGGER.info(f"Importing document {doc['import_id']}")
                create_dto = BulkImportDocumentDTO(**doc).to_document_create_dto()
                slug = generate_slug(
                    db=db, title=create_dto.title, created_slugs=document_slugs
                )
                import_id = document_repository.create(db, create_dto, slug)
                document_slugs.add(slug)
                document_import_ids.append(import_id)
                total_documents_saved += 1
            else:
                _LOGGER.info(f"Updating document {doc['import_id']}")
                update_dto = BulkImportDocumentDTO(**doc).to_document_write_dto()
                import_id = document_repository.update(db, doc["import_id"], update_dto)
                document_import_ids.append(import_id)
                # total_documents_saved += 1

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
        if not _find_entity_in_db(FamilyEvent, event["import_id"], db):
            _LOGGER.info(f"Importing event {event['import_id']}")
            dto = BulkImportEventDTO(**event).to_event_create_dto()
            event_metadata = create_event_metadata_object(
                db, corpus_import_id, event["event_type_value"], datetime_event_name
            )
            import_id = event_repository.create(db, dto, event_metadata)
            event_import_ids.append(import_id)
            total_events_saved += 1
        else:
            _LOGGER.info(f"Updating event {event['import_id']}")
            update_dto = BulkImportEventDTO(**event).to_event_write_dto()
            import_id = event_repository.update(db, event["import_id"], update_dto)
            event_import_ids.append(import_id)
            total_events_saved += 1

    _LOGGER.info(f"Saved {total_events_saved} events")
    return event_import_ids


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def import_data(
    data: dict[str, Any],
    corpus_import_id: str,
    document_limit: Optional[int] = None,
) -> None:
    """
    Imports data for a given corpus_import_id.

    :param dict[str, Any] data: The data to be imported.
    :param str corpus_import_id: The import_id of the corpus the data should be imported into.
    :param Optional[int] document_limit: The max number of documents to be saved in this session or None.
    :raises RepositoryError: raised on a database error.
    :raises ValidationError: raised should the data be invalid.
    """
    notification_service.send_notification(
        f"🚀 Bulk import for corpus: {corpus_import_id} has started."
    )
    end_message = ""

    import_uuid = uuid4()
    upload_bulk_import_json_to_s3(f"{import_uuid}-request", corpus_import_id, data)

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
            result["documents"] = save_documents(
                document_data,
                corpus_import_id,
                document_limit or DEFAULT_DOCUMENT_LIMIT,
                db,
            )
        if event_data:
            _LOGGER.info("Saving events")
            result["events"] = save_events(event_data, corpus_import_id, db)

        upload_bulk_import_json_to_s3(f"{import_uuid}-result", corpus_import_id, result)

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
