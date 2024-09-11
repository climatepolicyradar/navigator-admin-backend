import json
import logging
from io import BytesIO
from typing import Any, Dict

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class IngestJSONBuilder(BaseModel):
    data: Dict[str, Any] = {}

    def with_collection(
        self,
        import_id: str = "test.new.collection.0",
        title: str = "Test title",
        description: str = "Test description",
    ) -> "IngestJSONBuilder":
        """Add a collection to the JSON data."""

        self.data.setdefault("collections", []).append(
            {
                "import_id": import_id,
                "title": title,
                "description": description,
            }
        )
        return self

    def with_family(
        self,
        import_id: str = "test.new.family.0",
        title: str = "Test",
        summary: str = "Test",
        geographies: str = "South Asia",
        category: str = "UNFCCC",
        metadata: dict[str, Any] = {"author_type": ["Non-Party"], "author": ["Test"]},
        collections: list[str] = ["test.new.collection.0"],
    ) -> "IngestJSONBuilder":
        """Add a family to the JSON data."""

        self.data.setdefault("families", []).append(
            {
                "import_id": import_id,
                "title": title,
                "summary": summary,
                "geography": geographies,
                "category": category,
                "metadata": metadata,
                "collections": collections,
            }
        )
        return self

    def with_document(
        self,
        import_id: str = "test.new.document.0",
        family_import_id: str = "test.new.family.0",
        metadata: dict[str, Any] = {"role": ["MAIN"], "type": ["Law"]},
        variant_name: str = "Original Language",
        title: str = "",
        user_language_name: str = "",
    ) -> "IngestJSONBuilder":
        """Add a document to the JSON data."""

        self.data.setdefault("documents", []).append(
            {
                "import_id": import_id,
                "family_import_id": family_import_id,
                "metadata": metadata,
                "variant_name": variant_name,
                "title": title,
                "user_language_name": user_language_name,
            }
        )
        return self

    def with_event(
        self,
        import_id: str = "test.new.event.0",
        family_import_id: str = "test.new.family.0",
        event_title: str = "Test",
        date: str = "2024-01-01",
        event_type_value: str = "Amended",
    ) -> "IngestJSONBuilder":
        """Add a document to the JSON data."""

        self.data.setdefault("documents", []).append(
            {
                "import_id": import_id,
                "family_import_id": family_import_id,
                "event_title": event_title,
                "date": date,
                "event_type_value": event_type_value,
            }
        )
        return self

    def build(self) -> BytesIO:
        """Build the JSON data and return as BytesIO."""

        json_data = json.dumps(self.data).encode("utf-8")
        return BytesIO(json_data)
