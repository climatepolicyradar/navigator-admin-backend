from typing import Optional
from pytest import MonkeyPatch

from app.model.family import FamilyDTO
from unit_tests.helpers.family import get_family


def mock_get_all_families(_):
    return [get_family("test")]


def mock_get_family(_, import_id: str) -> Optional[FamilyDTO]:
    if import_id == "missing":
        return None
    return get_family(import_id)


def mock_search_families(_, q: str) -> list[FamilyDTO]:
    if q == "empty":
        return []
    else:
        return [get_family("search1")]


def mock_update_family(_, data: FamilyDTO) -> Optional[FamilyDTO]:
    if data.import_id != "missing":
        return data


def mock_create_family(_, data: FamilyDTO) -> Optional[FamilyDTO]:
    if data.import_id != "error":
        return data


def mock_delete_family(_, import_id: str) -> bool:
    return import_id != "missing"


def mock_family_repo(family_repo, monkeypatch: MonkeyPatch, mocker):
    monkeypatch.setattr(family_repo, "get", mock_get_family)
    mocker.spy(family_repo, "get")

    monkeypatch.setattr(family_repo, "all", mock_get_all_families)
    mocker.spy(family_repo, "all")

    monkeypatch.setattr(family_repo, "search", mock_search_families)
    mocker.spy(family_repo, "search")

    monkeypatch.setattr(family_repo, "update", mock_update_family)
    mocker.spy(family_repo, "update")

    monkeypatch.setattr(family_repo, "create", mock_create_family)
    mocker.spy(family_repo, "create")

    monkeypatch.setattr(family_repo, "delete", mock_delete_family)
    mocker.spy(family_repo, "delete")
