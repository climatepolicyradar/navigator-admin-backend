"""
Ingest Service

This layer uses the corpus, collection, family, document and event repos to handle bulk 
import of data and other services for validation etc.
"""

from typing import Optional

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


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def save_collections(
    collection_data: list[dict], corpus_import_id: str, db: Optional[Session] = None
) -> list[str]:
    """
    Creates new collections with the values passed.

    :param list[dict] collection_data: The data to use for creating collections.
    :param str corpus_import_id: The import_id of the corpus the collections belong to.
    :param Optional[Session] The database session to use for saving collections.
    :return str: The new import_ids for the saved collections.
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


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def save_families(
    family_data: list[dict], corpus_import_id: str, db: Optional[Session] = None
) -> list[str]:
    """
    Creates new families with the values passed.

    :param list[dict] families_data: The data to use for creating families.
    :param str corpus_import_id: The import_id of the corpus the families belong to.
    :param Optional[Session] The database session to use for saving families.
    :return str: The new import_ids for the saved families.
    """

    if db is None:
        db = db_session.get_db()

    validation.validate_families(family_data, corpus_import_id)

    family_import_ids = []
    org_id = corpus.get_corpus_org_id(corpus_import_id)

    for fam in family_data:
        # TODO: Uncomment when implementing feature/pdct-1402-validate-collection-exists-before-creating-family
        # collection.validate(collections, db)
        dto = IngestFamilyDTO(
            **fam, corpus_import_id=corpus_import_id
        ).to_family_create_dto(corpus_import_id)
        import_id = family_repository.create(
            db, dto, geography.get_id(db, dto.geography), org_id
        )
        family_import_ids.append(import_id)

    return family_import_ids


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def save_documents(
    document_data: list[dict],
    corpus_import_id: str,
    db: Optional[Session] = None,
) -> list[str]:
    """
    Creates new documents with the values passed.

    :param list[dict] document_data: The data to use for creating documents.
    :param str corpus_import_id: The import_id of the corpus the documents belong to.
    :param Optional[Session] The database session to use for saving documents.
    :return str: The new import_ids for the saved documents.
    """
    if db is None:
        db = db_session.get_db()

    validation.validate_documents(document_data, corpus_import_id)

    document_import_ids = []

    for doc in document_data:
        dto = IngestDocumentDTO(**doc).to_document_create_dto()
        import_id = document_repository.create(db, dto)
        document_import_ids.append(import_id)

    return document_import_ids


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def save_events(
    event_data: list[dict],
    corpus_import_id: str,
    db: Optional[Session] = None,
) -> list[str]:
    """
    Creates new events with the values passed.

    :param list[dict] event_data: The data to use for creating events.
    :param str corpus_import_id: The import_id of the corpus the events belong to.
    :param Optional[Session] The database session to use for saving events.
    :return str: The new import_ids for the saved events.
    """
    if db is None:
        db = db_session.get_db()

    validation.validate_events(event_data, corpus_import_id)

    event_import_ids = []

    for ev in event_data:
        dto = IngestEventDTO(**ev).to_event_create_dto()
        import_id = event_repository.create(db, dto)
        event_import_ids.append(import_id)

    return event_import_ids


def validate_entity_relationships(data: dict) -> None:
    families = []
    if "families" in data:
        for fam in data["families"]:
            families.append(fam["import_id"])

    documents = []
    if "documents" in data:
        for doc in data["documents"]:
            documents.append(doc["family_import_id"])

    family_document_set = set(families)
    unmatched = [x for x in documents if x not in family_document_set]
    if unmatched:
        raise ValidationError(f"No family with id {unmatched} found")


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def import_data(data: dict, corpus_import_id: str) -> dict:
    """
    Imports data for a given corpus_import_id.

    :param dict data: The data to be imported.
    :param str corpus_import_id: The import_id of the corpus the data should be imported into.
    :raises RepositoryError: raised on a database error.
    :raises ValidationError: raised should the data be invalid.
    :return dict: Import ids of the saved entities.
    """
    db = db_session.get_db()

    collection_data = data["collections"] if "collections" in data else None
    family_data = data["families"] if "families" in data else None
    document_data = data["documents"] if "documents" in data else None
    event_data = data["events"] if "events" in data else None

    if not data:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)

    response = {}

    try:
        validate_entity_relationships(data)

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
