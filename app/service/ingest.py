"""
Ingest Service

This layer uses the corpus, collection, family, document and event repos to handle bulk 
import of data and other services for validation etc.
"""

from typing import Optional

from db_client.models.dfce.taxonomy_entry import EntitySpecificTaxonomyKeys
from fastapi import HTTPException, status
from pydantic import ConfigDict, validate_call
from sqlalchemy.orm import Session

import app.clients.db.session as db_session
import app.repository.collection as collection_repository
import app.repository.family as family_repository
import app.service.category as category
import app.service.collection as collection
import app.service.corpus as corpus
import app.service.geography as geography
import app.service.metadata as metadata
from app.errors import ValidationError
from app.model.ingest import IngestCollectionDTO, IngestDocumentDTO, IngestFamilyDTO
from app.service.collection import validate_import_id


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def save_collections(
    collection_data: list[dict], corpus_import_id: str, db: Optional[Session] = None
) -> list[str]:
    """
    Creates new collections with the values passed.

    :param Session db: The database session to use for saving collections.
    :param list[dict] collection_data: The data to use for creating collections.
    :param str corpus_import_id: The import_id of the corpus the collections belong to.
    :return str: The new import_ids for the saved collections.
    """
    if db is None:
        db = db_session.get_db()

    collection_import_ids = []
    org_id = corpus.get_corpus_org_id(corpus_import_id)
    for coll in collection_data:
        dto = IngestCollectionDTO(**coll).to_collection_create_dto()
        if dto.import_id:
            validate_import_id(dto.import_id)
        import_id = collection_repository.create(db, dto, org_id)

        collection_import_ids.append(import_id)
    return collection_import_ids


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def save_families(
    family_data: list[dict], corpus_import_id: str, db: Optional[Session] = None
) -> list[str]:
    """
    Creates new families with the values passed.

    :param Session db: The database session to use for saving families.
    :param list[dict] families_data: The data to use for creating families.
    :param str corpus_import_id: The import_id of the corpus the families belong to.
    :return str: The new import_ids for the saved families.
    """

    if db is None:
        db = db_session.get_db()

    family_import_ids = []
    org_id = corpus.get_corpus_org_id(corpus_import_id)
    for fam in family_data:
        dto = IngestFamilyDTO(
            **fam, corpus_import_id=corpus_import_id
        ).to_family_create_dto(corpus_import_id)

        if dto.import_id:
            validate_import_id(dto.import_id)
        corpus.validate(db, corpus_import_id)
        geo_id = geography.get_id(db, dto.geography)
        category.validate(dto.category)
        collections = set(dto.collections)
        collection.validate_multiple_ids(collections)
        # TODO: Uncomment when implementing feature/pdct-1402-validate-collection-exists-before-creating-family
        # collection.validate(collections, db)
        metadata.validate_metadata(db, corpus_import_id, dto.metadata)

        import_id = family_repository.create(db, dto, geo_id, org_id)
        family_import_ids.append(import_id)
    return family_import_ids


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def save_documents(
    document_data: list[dict],
    corpus_import_id: str,
    family_document_mapping: dict,
    db: Optional[Session] = None,
) -> list[str]:
    """
    Creates new documents with the values passed.

    :param Session db: The database session to use for saving documents.
    :param list[dict] document_data: The data to use for creating documents.
    :param str corpus_import_id: The import_id of the corpus the documents belong to.
    :return str: The new import_ids for the saved documents.
    """
    if db is None:
        db = db_session.get_db()

    document_import_ids = []
    for doc in document_data:
        family_import_id = family_document_mapping[doc["import_id"]]
        # if not family_import_id:
        #     raise ValidationError(
        #         f"No family associated with document: {doc['import_id']}"
        #     )

        dto = IngestDocumentDTO(**doc).to_document_create_dto(family_import_id)

        if dto.variant_name == "":
            raise ValidationError("Variant name is empty")
        metadata.validate_metadata(
            db,
            corpus_import_id,
            dto.metadata,
            EntitySpecificTaxonomyKeys.DOCUMENT.value,
        )

        document_import_ids.append(dto.import_id)
    return document_import_ids


def validate_entity_relationships(data: dict) -> None:
    family_documents = []
    if "families" in data:
        for fam in data["families"]:
            family_documents.extend(fam["documents"])

    documents = []
    if "documents" in data:
        for doc in data["documents"]:
            documents.append(doc["import_id"])

    family_document_set = set(family_documents)
    unmatched = [x for x in documents if x not in family_document_set]
    if unmatched:
        raise ValidationError(f"No family found for document(s): {unmatched}")


def create_family_document_mapping(family_data: dict) -> dict:
    family_document_mapping = {}
    for fam in family_data:
        for doc in fam["documents"]:
            family_document_mapping[doc] = fam["import_id"]
    return family_document_mapping


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def import_data(data: dict, corpus_import_id: str) -> dict:
    """
    Imports data for a given corpus_import_id.

    :param dict data: The data to be imported.
    :param str corpus_import_id: The import_id of the corpus the data should be imported into.
    :raises RepositoryError: raised on a database error.
    :raises ValidationError: raised should the import_id be invalid.
    :return dict: Import ids of the saved entities.
    """
    db = db_session.get_db()

    collection_data = data["collections"] if "collections" in data else None
    family_data = data["families"] if "families" in data else None
    document_data = data["documents"] if "documents" in data else None

    if not data:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)

    response = {}

    try:
        validate_entity_relationships(data)

        family_document_mapping = {}
        if collection_data:
            response["collections"] = save_collections(
                collection_data, corpus_import_id, db
            )
        if family_data:
            response["families"] = save_families(family_data, corpus_import_id, db)
            family_document_mapping = create_family_document_mapping(family_data)
        if document_data:
            response["documents"] = save_documents(
                document_data, corpus_import_id, family_document_mapping, db
            )

        return response
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.commit()
