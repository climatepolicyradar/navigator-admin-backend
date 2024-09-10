from typing import Any, Optional

from db_client.functions.corpus_helpers import TaxonomyData, get_taxonomy_from_corpus
from db_client.models.dfce.taxonomy_entry import EntitySpecificTaxonomyKeys

import app.clients.db.session as db_session
import app.service.category as category
import app.service.collection as collection
import app.service.corpus as corpus
import app.service.metadata as metadata
from app.errors import ValidationError
from app.service.collection import validate_import_id


def validate_collection(collection: dict[str, Any]) -> None:
    """
    Validates a collection.

    :param dict[str, Any] collection: The collection object to be validated.
    :raises ValidationError: raised should the data be invalid.
    """
    validate_import_id(collection["import_id"])


def validate_collections(collections: list[dict[str, Any]]) -> None:
    """
    Validates a list of collections.

    :param list[dict[str, Any]] collections: The list of collection objects to be validated.
    """
    for coll in collections:
        validate_collection(coll)


def validate_family(family: dict[str, Any], corpus_import_id: str) -> None:
    """
    Validates a family.

    :param dict[str, Any] family: The family object to be validated.
    :raises ValidationError: raised should the data be invalid.
    """
    db = db_session.get_db()

    validate_import_id(family["import_id"])
    corpus.validate(db, corpus_import_id)
    category.validate(family["category"])
    collections = set(family["collections"])
    collection.validate_multiple_ids(collections)
    metadata.validate_metadata(db, corpus_import_id, family["metadata"])


def validate_families(families: list[dict[str, Any]], corpus_import_id: str) -> None:
    """
    Validates a list of families.

    :param list[dict[str, Any]] families: The list of family objects to be validated.
    """
    for fam in families:
        validate_family(fam, corpus_import_id)


def validate_document(document: dict[str, Any], corpus_import_id: str) -> None:
    """
    Validates a document.

    :param dict[str, Any] document: The document object to be validated.
    :raises ValidationError: raised should the data be invalid.
    """
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


def validate_documents(documents: list[dict[str, Any]], corpus_import_id: str) -> None:
    """
    Validates a list of documents.

    :param list[dict[str, Any]] documents: The list of document objects to be validated.
    """
    for doc in documents:
        validate_document(doc, corpus_import_id)


def validate_event(event: dict[str, Any], taxonomy: Optional[TaxonomyData]) -> None:
    """
    Validates an event.

    :param dict[str, Any] event: The event object to be validated.
    :raises ValidationError: raised should the data be invalid.
    """
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


def validate_events(events: list[dict[str, Any]], corpus_import_id: str) -> None:
    """
    Validates a list of events.

    :param list[dict[str, Any]] events: The list of event objects to be validated.
    """
    db = db_session.get_db()

    event_taxonomy = get_taxonomy_from_corpus(db, corpus_import_id)

    for ev in events:
        validate_event(ev, event_taxonomy)
