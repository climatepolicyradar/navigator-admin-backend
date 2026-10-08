"""
Bulk Import Service

This layer uses the corpus, collection, family, document and event repos to handle bulk
import of data and other services for validation etc.
"""

import logging
import math
import os
import time
from typing import Any, Optional
from uuid import UUID

from db_client.models.dfce.family import FamilyDocument
from db_client.models.dfce.taxonomy_entry import EntitySpecificTaxonomyKeys
from db_client.models.organisation.counters import CountedEntity
from pydantic import ConfigDict, validate_call
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
from app.clients.aws.s3bucket import (
    get_bulk_import_json_from_s3,
    upload_bulk_import_json_to_s3,
    upload_sql_db_dump_to_s3,
)
from app.errors import ValidationError
from app.model.bulk_import import (
    BulkImportCollectionDTO,
    BulkImportDocumentDTO,
    BulkImportEventDTO,
    BulkImportFamilyDTO,
    BulkImportStatus,
    BulkImportStatusDTO,
)
from app.repository.helpers import generate_slug
from app.service.database_dump import delete_local_file, get_database_dump

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())


def trigger_db_dump_upload_to_sql(thread_id: Optional[str]) -> None:
    dump_file = get_database_dump()
    try:
        upload_sql_db_dump_to_s3(dump_file)
    except Exception:
        notification_service.send_notification(
            "💥 Database Dump upload failed.", thread_id
        )
    finally:
        delete_local_file(dump_file)


def get_collection_template(corpus_type: str) -> dict:
    """
    Gets a collection template.

    :param str corpus_type: The corpus_type to use to get the collection template.
    :return dict: The collection template.
    """
    collection_schema = BulkImportCollectionDTO.model_json_schema(mode="serialization")
    collection_template = collection_schema["properties"]
    collection_template["metadata"] = get_metadata_template(
        corpus_type, CountedEntity.Collection
    )

    return collection_template


def get_event_template(corpus_type: str) -> dict:
    """
    Gets an event template.

    :return dict: The event template.
    """
    event_schema = BulkImportEventDTO.model_json_schema(mode="serialization")
    event_template = event_schema["properties"]

    event_meta = get_metadata_template(corpus_type, CountedEntity.Event)

    if "event_type" not in event_meta:
        raise ValidationError("Bad taxonomy in database")
    event_template["event_type_value"] = event_meta["event_type"]
    event_template["metadata"] = event_meta

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
    elif metadata_type == CountedEntity.Collection:
        return (
            metadata.pop(EntitySpecificTaxonomyKeys.COLLECTION.value)
            if metadata.get(EntitySpecificTaxonomyKeys.COLLECTION.value, None)
            else {}
        )
    elif metadata_type == CountedEntity.Family:
        metadata.pop(EntitySpecificTaxonomyKeys.DOCUMENT.value)
        metadata.pop(EntitySpecificTaxonomyKeys.EVENT.value)
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
    start_time = time.time()
    if db is None:
        with db_session.get_db() as session:
            return save_collections(collection_data, corpus_import_id, session)

    _LOGGER.info("🔍 Validating collection data...")
    validation.validate_collections(collection_data, corpus_import_id)
    _LOGGER.info("✅ Validation successful")

    collection_import_ids = []
    org_id = corpus.get_corpus_org_id(corpus_import_id)
    total_collections_saved = 0

    for coll in collection_data:
        import_id = coll["import_id"]
        existing_collection = collection_repository.get(db, import_id)
        if not existing_collection:
            _LOGGER.info(f"Importing collection {import_id}")
            create_dto = BulkImportCollectionDTO(**coll).to_collection_create_dto()
            collection_repository.create(db, create_dto, org_id)
            collection_import_ids.append(import_id)
            total_collections_saved += 1
        else:
            update_collection = BulkImportCollectionDTO(**coll)
            if update_collection.is_different_from(existing_collection):
                _LOGGER.info(f"Updating collection {import_id}")
                collection_repository.update(
                    db, import_id, update_collection.to_collection_write_dto()
                )
                collection_import_ids.append(import_id)
                total_collections_saved += 1

    _LOGGER.info(
        f"⏱️ Saved {total_collections_saved} collections in {_get_duration(start_time)} seconds"
    )
    return collection_import_ids


def _get_duration(start_time: float) -> int:
    """
    Calculate duration in seconds from time passed in till now.

    :param float start_time: The time to calculate duration from.
    :return int: The duration from time passed in until now rounded up to the nearest second.
    """

    return math.ceil(time.time() - start_time)


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
    start_time = time.time()
    if db is None:
        with db_session.get_db() as session:
            return save_families(family_data, corpus_import_id, session)

    _LOGGER.info("🔍 Validating family data...")
    validation.validate_families(family_data, corpus_import_id)
    _LOGGER.info("✅ Validation successful")

    family_import_ids = []
    org_id = corpus.get_corpus_org_id(corpus_import_id)
    total_families_saved = 0

    for fam in family_data:
        import_id = fam["import_id"]
        existing_family = family_repository.get(db, import_id)
        if not existing_family:
            _LOGGER.info(f"Importing family {import_id}")
            create_dto = BulkImportFamilyDTO(
                **fam, corpus_import_id=corpus_import_id
            ).to_family_create_dto(corpus_import_id)
            geo_ids = [geography.get_id(db, geo) for geo in create_dto.geographies]
            family_repository.create(db, create_dto, geo_ids, org_id)
            family_import_ids.append(import_id)
            total_families_saved += 1
        else:
            update_family = BulkImportFamilyDTO(
                **fam, corpus_import_id=corpus_import_id
            )
            if update_family.is_different_from(existing_family):
                _LOGGER.info(f"Updating family {import_id}")
                geo_ids = [
                    geography.get_id(db, geo) for geo in update_family.geographies
                ]
                family_repository.update(
                    db, import_id, update_family.to_family_write_dto(), geo_ids
                )
                family_import_ids.append(import_id)
                total_families_saved += 1

    _LOGGER.info(
        f"⏱️ Saved {total_families_saved} families in {_get_duration(start_time)} seconds"
    )

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
        with db_session.get_db() as session:
            return save_documents(document_data, corpus_import_id, session)

    start_time = time.time()
    _LOGGER.info("🔍 Validating document data...")
    validation.validate_documents(document_data, corpus_import_id)
    _LOGGER.info("✅ Validation successful")

    document_import_ids = []
    document_slugs = set()
    total_documents_saved = 0

    for doc in document_data:
        import_id = doc["import_id"]
        existing_document = document_repository.get(db, import_id)
        if not existing_document:
            _LOGGER.info(f"Importing document {import_id}")
            create_dto = BulkImportDocumentDTO(**doc).to_document_create_dto()
            slug = generate_slug(
                db=db, title=create_dto.title, created_slugs=document_slugs
            )
            document_repository.create(db, create_dto, slug)
            document_slugs.add(slug)
            document_import_ids.append(import_id)
            total_documents_saved += 1
        else:
            update_document = BulkImportDocumentDTO(**doc)
            if update_document.is_different_from(existing_document):
                _LOGGER.info(f"Updating document {import_id}")
                slug = generate_slug(
                    db=db, title=update_document.title, created_slugs=document_slugs
                )
                document_repository.update(
                    db, import_id, update_document.to_document_write_dto(), slug
                )
                document_slugs.add(slug)
                document_import_ids.append(import_id)
                total_documents_saved += 1

    _LOGGER.info(
        f"⏱️ Saved {total_documents_saved} documents in {_get_duration(start_time)} seconds"
    )
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
        with db_session.get_db() as session:
            return save_events(event_data, corpus_import_id, session)

    start_time = time.time()

    _LOGGER.info("🔍 Validating event data...")
    validation.validate_events(event_data, corpus_import_id)
    _LOGGER.info("✅ Validation successful")

    event_import_ids = []
    total_events_saved = 0

    for event in event_data:
        import_id = event["import_id"]
        existing_event = event_repository.get_single_event(db, import_id)
        if not existing_event:
            _LOGGER.info(f"Importing event {import_id}")
            dto = BulkImportEventDTO(**event).to_event_create_dto()
            event_repository.create(db, dto)
            event_import_ids.append(import_id)
            total_events_saved += 1
        else:
            update_event = BulkImportEventDTO(**event)
            existing_event_metadata = event_repository.get_event_metadata(
                db, event["import_id"]
            )
            if update_event.is_different_from(existing_event, existing_event_metadata):
                _LOGGER.info(f"Updating event {import_id}")
                event_repository.update(
                    db,
                    import_id,
                    update_event.to_event_write_dto(),
                )
                event_import_ids.append(import_id)
                total_events_saved += 1

    _LOGGER.info(
        f"⏱️ Saved {total_events_saved} events in {_get_duration(start_time)} seconds"
    )
    return event_import_ids


def _filter_event_data(
    event_data: list[dict[str, Any]], db: Session
) -> list[dict[str, Any]]:
    """
    Filters a list of event data based on the import ids of saved documents.
    It returns a list of event data objects that either relate to a document that has already been saved
    or are not linked to a document.

    :param list[dict[str, Any]] event_data: The event data to be filtered.
    :param Session db: The database session to use.
    :return list[dict[str, Any]]: A filtered list of event data.
    """
    filtered_event_data = [
        event
        for event in event_data
        if not event.get("family_document_import_id")
        or db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == event.get("family_document_import_id"))
        .one_or_none()
    ]

    return filtered_event_data


def _count_entities(data: dict[str, Any]) -> dict[str, int]:
    """
    Counts the entities saved by a bulk import.

    :param dict[str, Any] data: The data that was imported.
    :return dict[str, int]: The number of each entity that was saved.
    """
    return {
        "collections": len(data.get("collections", [])),
        "families": len(data.get("families", [])),
        "documents": len(data.get("documents", [])),
        "events": len(data.get("events", [])),
    }


def _create_summary(data: dict[str, Any]) -> str:
    """
    Creates a summary of the bulk import.

    :param dict[str, Any] data: The data that was imported.
    :return str: A summary of the bulk import.
    """
    if not data:
        return "🗒️ No data to import."

    counts = _count_entities(data)

    if not any(counts.values()):
        return "🗒️ No data to import."

    summary_lines = [f" {count} {item}" for item, count in counts.items()]
    return "🗒️ Saved\n" + ",\n".join(summary_lines)


def _record_outcome(
    import_id: UUID,
    corpus_import_id: str,
    data: dict[str, Any],
    result: dict[str, Any],
    error: Optional[str],
) -> None:
    """
    Record the outcome of a bulk import to S3, where the status endpoint reads it from.

    A success writes the request and result files, even when there was no data to
    import, and a failure writes a failure file. Failures to record are logged and
    swallowed, so they never fail an import nor mask the error that caused one to fail.

    :param UUID import_id: The id of this bulk import.
    :param str corpus_import_id: The import_id of the corpus the data was imported into.
    :param dict[str, Any] data: The data that was imported.
    :param dict[str, Any] result: The import_ids saved by the import.
    :param Optional[str] error: The error the import failed with, or None if it succeeded.
    """
    try:
        if error is None:
            upload_bulk_import_json_to_s3(
                f"{import_id}-request", corpus_import_id, data
            )
            upload_bulk_import_json_to_s3(
                f"{import_id}-result", corpus_import_id, result
            )
        else:
            upload_bulk_import_json_to_s3(
                f"{import_id}-failure", corpus_import_id, {"error": error}
            )
    except Exception as e:
        _LOGGER.error(f"💥 Failed to record bulk import outcome caused by: {e}")


def get_import_status(import_id: UUID) -> BulkImportStatusDTO:
    """
    Get the status of a bulk import from the files it writes to S3 once finished.

    An import with neither a result nor a failure file is still running, or was never
    issued, or its container died before it could record an outcome.

    :param UUID import_id: The id of the bulk import.
    :return BulkImportStatusDTO: The status of the bulk import.
    """
    result = get_bulk_import_json_from_s3(f"{import_id}-result")
    if result is not None:
        return BulkImportStatusDTO(
            import_id=str(import_id),
            status=BulkImportStatus.SUCCESS,
            counts=_count_entities(result),
        )

    failure = get_bulk_import_json_from_s3(f"{import_id}-failure")
    if failure is not None:
        return BulkImportStatusDTO(
            import_id=str(import_id),
            status=BulkImportStatus.FAILURE,
            error=failure.get("error"),
        )

    return BulkImportStatusDTO(
        import_id=str(import_id), status=BulkImportStatus.RUNNING
    )


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def import_data(
    data: dict[str, Any],
    corpus_import_id: str,
    import_id: UUID,
) -> None:
    """
    Imports data for a given corpus_import_id.

    :param dict[str, Any] data: The data to be imported.
    :param str corpus_import_id: The import_id of the corpus the data should be imported into.
    :param UUID import_id: The id of this bulk import, which its outcome is recorded against.
    :raises RepositoryError: raised on a database error.
    :raises ValidationError: raised should the data be invalid.
    """
    start_time = time.time()
    thread_id = notification_service.send_notification(
        f"🚀 Bulk import for corpus: {corpus_import_id} has started."
    )
    end_message = ""
    error: Optional[str] = None

    _LOGGER.info("Getting DB session")
    with db_session.get_db() as db:
        collection_data = data["collections"] if "collections" in data else None
        family_data = data["families"] if "families" in data else None
        document_data = data["documents"] if "documents" in data else None
        event_data = data["events"] if "events" in data else None

        result = {}

        try:
            if collection_data:
                _LOGGER.info("💾 Saving collections")
                result["collections"] = save_collections(
                    collection_data, corpus_import_id, db
                )
            if family_data:
                _LOGGER.info("💾 Saving families")
                result["families"] = save_families(family_data, corpus_import_id, db)
            if document_data:
                _LOGGER.info("💾 Saving documents")
                result["documents"] = save_documents(
                    document_data,
                    corpus_import_id,
                    db,
                )
            if event_data:
                _LOGGER.info("💾 Saving events")
                result["events"] = save_events(
                    _filter_event_data(event_data, db),
                    corpus_import_id,
                    db,
                )

            db.commit()

            if not any([collection_data, family_data, document_data, event_data]):
                _LOGGER.info("🗒️ No data to import.")

            end_message = f"🎉 Bulk import for corpus: {corpus_import_id} successfully completed in {_get_duration(start_time)} seconds.\n{_create_summary(result)}"
        except Exception as e:
            _LOGGER.error(
                f"💥 Rolling back transaction due to the following error: {e}",
                exc_info=True,
            )
            db.rollback()
            error = str(e)
            group_id = os.environ.get(
                "SLACK_GROUP_ID_APPLICATION_ENGINEERS", ""
            ).strip()
            mention = f"<!subteam^{group_id}> " if group_id else ""
            end_message = (
                f"{mention}💥 Bulk import for corpus: {corpus_import_id} has failed."
            )
        finally:
            notification_service.send_notification(end_message, thread_id)
            trigger_db_dump_upload_to_sql(thread_id)
            # recorded after the dump, so callers only see an outcome once it's done
            _record_outcome(import_id, corpus_import_id, data, result, error)
