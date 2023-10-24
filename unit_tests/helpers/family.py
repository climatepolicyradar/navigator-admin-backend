from typing import Optional
from app.clients.db.models.law_policy.family import FamilyCategory
from app.model.family import FamilyCreateDTO, FamilyReadDTO, FamilyWriteDTO


def create_family_dto(
    import_id: str,
    title: str = "title",
    summary: str = "summary",
    geography: str = "CHN",
    category: str = FamilyCategory.LEGISLATIVE.value,
    metadata: Optional[dict] = None,
    slug: str = "slug",
) -> FamilyReadDTO:
    if metadata is None:
        metadata = {}
    return FamilyReadDTO(
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
        organisation="CCLW",
    )


def create_family_create_dto(
    title: str = "title",
    summary: str = "summary",
    geography: str = "CHN",
    category: str = FamilyCategory.LEGISLATIVE.value,
    metadata: Optional[dict] = None,
) -> FamilyCreateDTO:
    if metadata is None:
        metadata = {}
    return FamilyCreateDTO(
        title=title,
        summary=summary,
        geography=geography,
        category=category,
        metadata=metadata,
    )


def create_family_write_dto(
    title: str = "title",
    summary: str = "summary",
    geography: str = "CHN",
    category: str = FamilyCategory.LEGISLATIVE.value,
    metadata: Optional[dict] = None,
) -> FamilyWriteDTO:
    if metadata is None:
        metadata = {}
    return FamilyWriteDTO(
        title=title,
        summary=summary,
        geography=geography,
        category=category,
        metadata=metadata,
    )
