from typing import Optional
from app.clients.db.models.law_policy.family import FamilyCategory
from app.model.family import FamilyDTO


def create_family_dto(
    import_id: str,
    title: str = "title",
    summary: str = "summary",
    geography: str = "CHN",
    category: FamilyCategory = FamilyCategory.LEGISLATIVE,
    metadata: Optional[dict] = None,
    slug: str = "slug",
) -> FamilyDTO:
    if metadata is None:
        metadata = {}
    return FamilyDTO(
        import_id=import_id,
        title=title,
        summary=summary,
        geography=geography,
        category=category,
        status="status",
        metadata=metadata,
        slug=slug,
        events=["e1", "e2"],
        published_date=None,
        last_updated_date=None,
        documents=["doc1", "doc2"],
        collections=["col1", "col2"],
        organisation="test_org",
    )
