from datetime import datetime
from typing import Optional
from app.model.family import FamilyResponse


def get_family(import_id: str) -> Optional[FamilyResponse]:
    if import_id == "missing":
        return None

    return FamilyResponse(
        import_id=import_id,
        title="title",
        summary="summary",
        geography="geo",
        category="category",
        status="status",
        metadata={},
        slug="slug",
        events=["e1", "e2"],
        published_date=datetime.now(),
        last_updated_date=datetime.now(),
        documents=["doc1", "doc2"],
        collections=["col1", "col2"],
    )
