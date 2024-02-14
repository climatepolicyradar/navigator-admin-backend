from datetime import datetime
from typing import Optional
from db_client.models.law_policy.family import FamilyCategory
from app.model.family import FamilyCreateDTO, FamilyReadDTO, FamilyWriteDTO


def create_family_dto(
    import_id: str,
    title: str = "title",
    summary: str = "summary",
    geography: str = "CHN",
    category: str = FamilyCategory.LEGISLATIVE.value,
    metadata: Optional[dict] = None,
    slug: str = "slug",
    collections: Optional[list[str]] = ["x.y.z.1", "x.y.z.2"],
) -> FamilyReadDTO:
    if metadata is None:
        metadata = {}

    if collections is None:
        collections = []

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
        collections=collections,
        organisation="CCLW",
        created=datetime.now(),
        last_modified=datetime.now(),
    )


def create_family_create_dto(
    title: str = "title",
    summary: str = "summary",
    geography: str = "CHN",
    category: str = FamilyCategory.LEGISLATIVE.value,
    metadata: Optional[dict] = None,
    collections: list[str] = [],
) -> FamilyCreateDTO:
    if metadata is None:
        metadata = {}
    return FamilyCreateDTO(
        title=title,
        summary=summary,
        geography=geography,
        category=category,
        metadata=metadata,
        collections=collections,
    )


def create_family_write_dto(
    title: str = "title",
    summary: str = "summary",
    geography: str = "CHN",
    category: str = FamilyCategory.LEGISLATIVE.value,
    metadata: Optional[dict] = None,
    collections: list[str] = [],
) -> FamilyWriteDTO:
    if metadata is None:
        metadata = {}
    return FamilyWriteDTO(
        title=title,
        summary=summary,
        geography=geography,
        category=category,
        metadata=metadata,
        collections=collections,
    )
