from datetime import datetime
from typing import Optional

from db_client.models.dfce.family import FamilyCategory

from app.model.family import FamilyCreateDTO, FamilyReadDTO, FamilyWriteDTO


def create_family_read_dto(
    import_id: str,
    title: str = "title",
    summary: str = "summary",
    geography: Optional[str] = "CHN",
    geographies: list[str] = ["CHN", "BRB", "BHS"],
    category: str = FamilyCategory.LEGISLATIVE.value,
    metadata: Optional[dict] = None,
    slug: str = "slug",
    collections: Optional[list[str]] = None,
) -> FamilyReadDTO:
    if metadata is None:
        metadata = {
            "topic": [],
            "hazard": [],
            "sector": [],
            "keyword": [],
            "framework": [],
            "instrument": [],
        }

    if collections is None:
        collections = []

    return FamilyReadDTO(
        import_id=import_id,
        title=title,
        summary=summary,
        geography=geography,
        geographies=geographies,
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
        corpus_import_id="CCLW.corpus.i00000001.n0000",
        corpus_title="CCLW national policies",
        corpus_type="Laws and Policies",
        created=datetime.now(),
        last_modified=datetime.now(),
    )


def create_family_create_dto(
    title: str = "title",
    summary: str = "summary",
    geography: str = "CHN",
    geographies: list[str] = ["CHN"],
    category: str = FamilyCategory.LEGISLATIVE.value,
    metadata: Optional[dict] = None,
    collections: Optional[list[str]] = None,
    corpus_import_id: str = "CCLW.corpus.i00000001.n0000",
) -> FamilyCreateDTO:
    if metadata is None:
        metadata = {
            "topic": [],
            "hazard": [],
            "sector": [],
            "keyword": [],
            "framework": [],
            "instrument": [],
        }
    if collections is None:
        collections = []
    return FamilyCreateDTO(
        title=title,
        summary=summary,
        geography=geography,
        geographies=geographies,
        category=category,
        metadata=metadata,
        collections=collections,
        corpus_import_id=corpus_import_id,
    )


def create_family_write_dto(
    title: str = "title",
    summary: str = "summary",
    geography: Optional[str] = None,
    geographies: list[str] = ["CHN"],
    category: str = FamilyCategory.LEGISLATIVE.value,
    metadata: Optional[dict] = None,
    collections: Optional[list[str]] = None,
    concepts: Optional[list[dict]] = None,
) -> FamilyWriteDTO:
    if metadata is None:
        metadata = {
            "topic": [],
            "hazard": [],
            "sector": [],
            "keyword": [],
            "framework": [],
            "instrument": [],
        }
    if collections is None:
        collections = []
    return FamilyWriteDTO(
        title=title,
        summary=summary,
        geography=geography,
        geographies=geographies,
        category=category,
        metadata=metadata,
        collections=collections,
        concepts=concepts,
    )
