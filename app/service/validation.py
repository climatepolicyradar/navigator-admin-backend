from typing import Any

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
    :param str corpus_import_id: The corpus_import_id to be used for validating the family object.
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
    :param str corpus_import_id: The corpus_import_id to be used for validating the family objects.
    """
    for fam in families:
        validate_family(fam, corpus_import_id)


def validate_document(document: dict[str, Any], corpus_import_id: str) -> None:
    """
    Validates a document.

    :param dict[str, Any] document: The document object to be validated.
    :param str corpus_import_id: The corpus_import_id to be used for validating the document object.
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
    :param str corpus_import_id: The corpus_import_id to be used for validating the document objects.
    """
    for doc in documents:
        validate_document(doc, corpus_import_id)


def validate_event(event: dict[str, Any], corpus_import_id: str) -> None:
    """
    Validates an event.

    :param dict[str, Any] event: The event object to be validated.
    :param str corpus_import_id: The corpus_import_id to be used for
        validating the event object.
    :raises ValidationError: raised should the data be invalid.
    """
    validate_import_id(event["import_id"])
    validate_import_id(event["family_import_id"])

    db = db_session.get_db()
    metadata.validate_metadata(
        db,
        corpus_import_id,
        event["event_type_value"],
        EntitySpecificTaxonomyKeys.EVENT.value,
    )


def validate_events(events: list[dict[str, Any]], corpus_import_id: str) -> None:
    """
    Validates a list of events.

    :param list[dict[str, Any]] events: The list of event objects to be
        validated.
    :param str corpus_import_id: The corpus_import_id to be used for
        validating the event objects.
    """
    for ev in events:
        validate_event(ev, corpus_import_id)
