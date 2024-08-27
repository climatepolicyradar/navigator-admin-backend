"""
Ingest Service

This layer uses the corpus, collection, family, document and event repos to handle bulk 
import of data and other services for validation etc.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

import app.clients.db.session as db_session
import app.repository.collection as collection
import app.service.corpus as corpus
from app.model.ingest import IngestCollectionDTO, IngestFamilyDTO
from app.service.collection import validate_import_id


def save_collections(
    db: Session, collection_data: list[dict], org_id: int
) -> list[str]:
    collection_import_ids = []
    for coll in collection_data:
        dto = IngestCollectionDTO(**coll).to_collection_create_dto()
        if dto.import_id:
            validate_import_id(dto.import_id)
        import_id = collection.create(db, dto, org_id)
        collection_import_ids.append(import_id)
    return collection_import_ids


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

    if not data:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)

    family_import_ids = []
    response = {}
    org_id = corpus.get_corpus_org_id(corpus_import_id)
    if collection_data:
        response["collections"] = save_collections(db, collection_data, org_id)
    if family_data:
        for fam in family_data:
            IngestFamilyDTO(
                **fam, corpus_import_id=corpus_import_id
            ).to_family_create_dto(corpus_import_id)
            # import_id = family.create(dto, org_id)
            family_import_ids.append("created")
            response["families"] = family_import_ids

    return response
