from db_client.models.dfce.taxonomy_entry import EntitySpecificTaxonomyKeys

import app.clients.db.session as db_session
import app.service.category as category
import app.service.collection as collection
import app.service.corpus as corpus
import app.service.metadata as metadata
from app.errors import ValidationError
from app.service.collection import validate_import_id


def validate_collection(collection: dict) -> None:
    validate_import_id(collection["import_id"])


def validate_family(family: dict, corpus_import_id: str) -> None:
    db = db_session.get_db()

    validate_import_id(family["import_id"])
    corpus.validate(db, corpus_import_id)
    category.validate(family["category"])
    collections = set(family["collections"])
    collection.validate_multiple_ids(collections)
    metadata.validate_metadata(db, corpus_import_id, family["metadata"])


def validate_document(document: dict, corpus_import_id: str) -> None:
    db = db_session.get_db()

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
