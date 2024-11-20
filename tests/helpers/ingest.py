import json
import logging
from io import BytesIO
from typing import Any

logger = logging.getLogger(__name__)


default_collection = {
    "import_id": "test.new.collection.0",
    "title": "Test title",
    "description": "Test description",
}


def custom_collection(updates: dict[str, Any]) -> dict[str, Any]:
    new_collection = default_collection.copy()
    new_collection.update(updates)
    return new_collection


default_family = {
    "import_id": "test.new.family.0",
    "title": "Test",
    "summary": "Test",
    "geographies": ["South Asia"],
    "category": "UNFCCC",
    "metadata": {"author_type": ["Non-Party"], "author": ["Test"]},
    "collections": ["test.new.collection.0"],
}


def custom_family(updates: dict[str, Any]) -> dict[str, Any]:
    new_family = default_family.copy()
    new_family.update(updates)
    return new_family


default_document = {
    "import_id": "test.new.document.0",
    "family_import_id": "test.new.family.0",
    "metadata": {"role": ["MAIN"], "type": ["Law"]},
    "variant_name": None,
    "title": "",
    "user_language_name": "",
}


def custom_document(updates: dict[str, Any]) -> dict[str, Any]:
    new_document = default_document.copy()
    new_document.update(updates)
    return new_document


default_event = {
    "import_id": "test.new.event.0",
    "family_import_id": "test.new.family.0",
    "event_title": "Test",
    "date": "2024-01-01",
    "event_type_value": "Amended",
}


def custom_event(updates: dict[str, Any]) -> dict[str, Any]:
    new_event = default_event.copy()
    new_event.update(updates)
    return new_event


def build_json_file(data: dict[str, Any]) -> BytesIO:
    json_data = json.dumps(data).encode("utf-8")
    return BytesIO(json_data)
