from typing import Optional
from pytest import MonkeyPatch

from app.model.family import FamilyDTO


def get_family(import_id: str) -> FamilyDTO:
    return FamilyDTO(
        import_id=import_id,
        title="title",
        summary="summary",
        geography="geo",
        category="category",
        status="status",
        metadata={},
        slug="slug",
        events=["e1", "e2"],
        published_date=None,
        last_updated_date=None,
        documents=["doc1", "doc2"],
        collections=["col1", "col2"],
    )


def mock_get_all_families():
    return [get_family("test")]


def mock_get_family(import_id: str) -> Optional[FamilyDTO]:
    if import_id == "missing":
        return None
    return get_family(import_id)


def mock_search_families(q: str) -> list[FamilyDTO]:
    if q == "empty":
        return []
    else:
        return [get_family("search1")]


def mock_update_family(import_id: str, data: FamilyDTO) -> Optional[FamilyDTO]:
    if import_id != "missing":
        return data


def mock_create_family(data: FamilyDTO) -> Optional[FamilyDTO]:
    if data.import_id != "missing":
        return data


def mock_delete_family(import_id: str) -> bool:
    return import_id != "missing"


def mock_family_service(family_service, monkeypatch: MonkeyPatch, mocker):
    monkeypatch.setattr(family_service, "get_family", mock_get_family)
    mocker.spy(family_service, "get_family")

    monkeypatch.setattr(family_service, "get_all_families", mock_get_all_families)
    mocker.spy(family_service, "get_all_families")

    monkeypatch.setattr(family_service, "search_families", mock_search_families)
    mocker.spy(family_service, "search_families")

    monkeypatch.setattr(family_service, "update_family", mock_update_family)
    mocker.spy(family_service, "update_family")

    monkeypatch.setattr(family_service, "create_family", mock_create_family)
    mocker.spy(family_service, "create_family")

    monkeypatch.setattr(family_service, "delete_family", mock_delete_family)
    mocker.spy(family_service, "delete_family")
