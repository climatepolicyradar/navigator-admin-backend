"""
Ingest Service

This layer uses the corpus, collection, family, document and event repos to handle bulk 
import of data and other services for validation etc.
"""

from fastapi import HTTPException, status

import app.service.collection as collection
import app.service.corpus as corpus
from app.errors import ValidationError
from app.model.ingest import IngestCollectionDTO, IngestFamilyDTO


def import_data(data: dict, corpus_import_id: str) -> dict:
    """
    Imports data for a given corpus_import_id.

    :param dict data: The data to be imported.
    :param str corpus_import_id: The import_id of the corpus the data should be imported into.
    :raises RepositoryError: raised on a database error.
    :raises ValidationError: raised should the import_id be invalid.
    :return dict: Import ids of the saved entities.
    """
    collection_data = data["collections"] if "collections" in data else None
    family_data = data["families"] if "families" in data else None

    if not data:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)

    collection_import_ids = []
    family_import_ids = []
    response = {}
    try:
        org_id = corpus.get_corpus_org_id(corpus_import_id)
        if collection_data:
            for coll in collection_data:
                dto = IngestCollectionDTO(**coll).to_collection_create_dto()
                import_id = collection.create(dto, org_id)
                collection_import_ids.append(import_id)
                response["collections"] = collection_import_ids
        if family_data:
            for fam in family_data:
                dto = IngestFamilyDTO(
                    **fam, corpus_import_id=corpus_import_id
                ).to_family_create_dto(corpus_import_id)
                # import_id = family.create(dto, org_id)
                family_import_ids.append("created")
                response["families"] = family_import_ids

        return response
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
