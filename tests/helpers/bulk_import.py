import json
import logging
from io import BytesIO
from typing import Any

logger = logging.getLogger(__name__)


default_collection = {
    "import_id": "test.new.collection.0",
    "title": "Test title",
    "description": "Test description",
    "metadata": {},
}


default_family = {
    "import_id": "test.new.family.0",
    "title": "Test title",
    "summary": "Test",
    "geographies": ["XAA"],
    "category": "UNFCCC",
    "metadata": {"author_type": ["Non-Party"], "author": ["Test"]},
    "collections": ["test.new.collection.0"],
}


default_document = {
    "import_id": "test.new.document.0",
    "family_import_id": "test.new.family.0",
    "metadata": {"role": ["MAIN"], "type": ["Law"]},
    "variant_name": None,
    "title": "Test title",
    "user_language_name": "Spanish",
    "source_url": None,
}


default_event = {
    "import_id": "test.new.event.0",
    "family_import_id": "test.new.family.0",
    "event_title": "Test title",
    "date": "2024-01-01",
    "event_type_value": "Amended",
    "metadata": {"event_type": ["Amended"], "datetime_event_name": ["Passed/Approved"]},
}


def build_json_file(data: dict[str, Any]) -> BytesIO:
    json_data = json.dumps(data).encode("utf-8")
    return BytesIO(json_data)
