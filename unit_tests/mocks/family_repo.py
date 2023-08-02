from typing import Optional
from pytest import MonkeyPatch

from app.model.family import FamilyDTO
from unit_tests.helpers.family import create_family_dto


MISSING_ID = "A.0.0.0"
VALID_ID = "A.0.0.1"
FAIL_ID = "F.F.F.F"


def mock_get_all_families(_):
    return [create_family_dto("test")]


def mock_get_family(_, import_id: str) -> Optional[FamilyDTO]:
    if import_id == MISSING_ID:
        return None
    return create_family_dto(import_id)


def mock_search_families(_, q: str) -> list[FamilyDTO]:
    if q == "empty":
        return []
    else:
        return [create_family_dto("search1")]


def mock_update_family(_, data: FamilyDTO, __) -> Optional[FamilyDTO]:
    if data.import_id != MISSING_ID:
        return data


def mock_create_family(_, data: FamilyDTO, __, ___) -> Optional[FamilyDTO]:
    if data.import_id != FAIL_ID:
        return data


def mock_delete_family(_, import_id: str) -> bool:
    return import_id != MISSING_ID


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
