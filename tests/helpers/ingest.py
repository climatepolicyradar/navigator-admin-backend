import json
import logging
from io import BytesIO
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


def bulk_import_json_builder():
    data = {}

    def with_collection(
        import_id: str = "test.new.collection.0",
        title: str = "Test title",
        description: str = "Test description",
    ) -> Callable:
        data.setdefault("collections", []).append(
            {
                "import_id": import_id,
                "title": title,
                "description": description,
            }
        )
        return with_collection

    def with_family(
        import_id: str = "test.new.family.0",
        title: str = "Test",
        summary: str = "Test",
        geographies: list[str] = ["South Asia"],
        category: str = "UNFCCC",
        metadata: dict[str, Any] = {"author_type": ["Non-Party"], "author": ["Test"]},
        collections: list[str] = ["test.new.collection.0"],
    ) -> Callable:
        data.setdefault("families", []).append(
            {
                "import_id": import_id,
                "title": title,
                "summary": summary,
                "geographies": geographies,
                "category": category,
                "metadata": metadata,
                "collections": collections,
            }
        )
        return with_family

    def with_document(
        import_id: str = "test.new.document.0",
        family_import_id: str = "test.new.family.0",
        metadata: dict[str, Any] = {"role": ["MAIN"], "type": ["Law"]},
        variant_name: Optional[str] = None,
        title: str = "",
        user_language_name: str = "",
    ) -> Callable:
        """Add a document to the JSON data."""

        data.setdefault("documents", []).append(
            {
                "import_id": import_id,
                "family_import_id": family_import_id,
                "metadata": metadata,
                "variant_name": variant_name,
                "title": title,
                "user_language_name": user_language_name,
            }
        )
        return with_document

    def with_event(
        import_id: str = "test.new.event.0",
        family_import_id: str = "test.new.family.0",
        event_title: str = "Test",
        date: str = "2024-01-01",
        event_type_value: str = "Amended",
    ) -> Callable:
        """Add a document to the JSON data."""

        data.setdefault("events", []).append(
            {
                "import_id": import_id,
                "family_import_id": family_import_id,
                "event_title": event_title,
                "date": date,
                "event_type_value": event_type_value,
            }
        )
        return with_event

    def build() -> BytesIO:
        json_data = json.dumps(data).encode("utf-8")
        return BytesIO(json_data)

    return with_collection, with_family, with_document, with_event, build
