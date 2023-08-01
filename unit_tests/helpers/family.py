from app.db.models.law_policy.family import FamilyCategory
from app.model.family import FamilyDTO


def create_family_dto(
    import_id: str, title: str = "title", summary: str = "summary"
) -> FamilyDTO:
    return FamilyDTO(
        import_id=import_id,
        title=title,
        summary=summary,
        geography="CHN",
        category=FamilyCategory.LEGISLATIVE,
        status="status",
        metadata={},
        slug="slug",
        events=["e1", "e2"],
        published_date=None,
        last_updated_date=None,
        documents=["doc1", "doc2"],
        collections=["col1", "col2"],
    )
