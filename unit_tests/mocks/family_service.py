from typing import Optional
from pytest import MonkeyPatch

from app.model.family import FamilyDTO
from unit_tests.helpers.family import create_family_dto


def mock_get_all_families():
    return [create_family_dto("test")]


def mock_get_family(import_id: str) -> Optional[FamilyDTO]:
    if import_id == "missing":
        return None
    return create_family_dto(import_id)


def mock_search_families(q: str) -> list[FamilyDTO]:
    if q == "empty":
        return []
    else:
        return [create_family_dto("search1")]


def mock_update_family(data: FamilyDTO) -> Optional[FamilyDTO]:
    if data.import_id != "missing":
        return data


def mock_create_family(data: FamilyDTO) -> Optional[FamilyDTO]:
    if data.import_id != "missing":
        return data


def mock_delete_family(import_id: str) -> bool:
    return import_id != "missing"


def mock_family_service(family_service, monkeypatch: MonkeyPatch, mocker):
    monkeypatch.setattr(family_service, "get", mock_get_family)
    mocker.spy(family_service, "get")

    monkeypatch.setattr(family_service, "all", mock_get_all_families)
    mocker.spy(family_service, "all")

    monkeypatch.setattr(family_service, "search", mock_search_families)
    mocker.spy(family_service, "search")

    monkeypatch.setattr(family_service, "update", mock_update_family)
    mocker.spy(family_service, "update")

    monkeypatch.setattr(family_service, "create", mock_create_family)
    mocker.spy(family_service, "create")

    monkeypatch.setattr(family_service, "delete", mock_delete_family)
    mocker.spy(family_service, "delete")
