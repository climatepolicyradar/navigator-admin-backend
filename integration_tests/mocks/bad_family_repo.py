from typing import Optional
from pytest import MonkeyPatch
from app.errors.repository_error import RepositoryError

from app.model.family import FamilyDTO


def mock_get_all_families(_):
    raise RepositoryError("Bad Repo")


def mock_get_family(_, import_id: str) -> Optional[FamilyDTO]:
    raise RepositoryError("Bad Repo")


def mock_search_families(_, q: str) -> list[FamilyDTO]:
    raise RepositoryError("Bad Repo")


def mock_update_family(_, data: FamilyDTO, __) -> Optional[FamilyDTO]:
    raise RepositoryError("Bad Repo")


def mock_create_family(_, data: FamilyDTO, __, ___) -> Optional[FamilyDTO]:
    raise RepositoryError("Bad Repo")


def mock_delete_family(_, import_id: str) -> bool:
    raise RepositoryError("Bad Repo")


def mock_bad_family_repo(family_repo, monkeypatch: MonkeyPatch, mocker):
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
