from typing import Optional

from db_client.functions.corpus_helpers import TaxonomyData, get_taxonomy_from_corpus
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


def validate_collections(collections: list[dict]) -> None:
    for coll in collections:
        validate_collection(coll)


def validate_family(family: dict, corpus_import_id: str) -> None:
    db = db_session.get_db()

    validate_import_id(family["import_id"])
    corpus.validate(db, corpus_import_id)
    category.validate(family["category"])
    collections = set(family["collections"])
    collection.validate_multiple_ids(collections)
    metadata.validate_metadata(db, corpus_import_id, family["metadata"])


def validate_families(families: list[dict], corpus_import_id: str) -> None:
    for fam in families:
        validate_family(fam, corpus_import_id)


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


def validate_documents(documents: list[dict], corpus_import_id: str) -> None:
    for doc in documents:
        validate_document(doc, corpus_import_id)


def validate_event(event: dict, taxonomy: Optional[TaxonomyData]) -> None:
    validate_import_id(event["import_id"])
    validate_import_id(event["family_import_id"])
    allowed_event_types = taxonomy["event_type"]["allowed_values"] if taxonomy else None
    if not allowed_event_types:
        raise ValidationError(
            f"No allowed event types found for event {event['import_id']}"
        )
    if (
        isinstance(allowed_event_types, list)
        and event["event_type_value"] not in allowed_event_types
    ):
        raise ValidationError(f"Event type ['{event['event_type_value']}'] is invalid!")


def validate_events(events: list[dict], corpus_import_id: str) -> None:
    db = db_session.get_db()

    event_taxonomy = get_taxonomy_from_corpus(db, corpus_import_id)

    for ev in events:
        validate_event(ev, event_taxonomy)
