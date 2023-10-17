from typing import Optional
from pytest import MonkeyPatch
from app.errors import RepositoryError

from app.model.family import FamilyReadDTO


def mock_bad_family_repo(repo, monkeypatch: MonkeyPatch, mocker):
    def mock_get_all(_):
        raise RepositoryError("Bad Repo")

    def mock_get(_, import_id: str) -> Optional[FamilyReadDTO]:
        raise RepositoryError("Bad Repo")

    def mock_search(_, q: str) -> list[FamilyReadDTO]:
        raise RepositoryError("Bad Repo")

    def mock_update(
        _, import_id: str, data: FamilyReadDTO, __
    ) -> Optional[FamilyReadDTO]:
        raise RepositoryError("Bad Repo")

    def mock_create(_, data: FamilyReadDTO, __, ___) -> Optional[FamilyReadDTO]:
        raise RepositoryError("Bad Repo")

    def mock_delete(_, import_id: str) -> bool:
        raise RepositoryError("Bad Repo")

    def mock_get_count(_) -> Optional[int]:
        raise RepositoryError("Bad Repo")

    monkeypatch.setattr(repo, "get", mock_get)
    mocker.spy(repo, "get")

    monkeypatch.setattr(repo, "all", mock_get_all)
    mocker.spy(repo, "all")

    monkeypatch.setattr(repo, "search", mock_search)
    mocker.spy(repo, "search")

    monkeypatch.setattr(repo, "update", mock_update)
    mocker.spy(repo, "update")

    monkeypatch.setattr(repo, "create", mock_create)
    mocker.spy(repo, "create")

    monkeypatch.setattr(repo, "delete", mock_delete)
    mocker.spy(repo, "delete")

    monkeypatch.setattr(repo, "count", mock_get_count)
    mocker.spy(repo, "count")


def mock_family_count_none(repo, monkeypatch: MonkeyPatch, mocker):
    def mock_get_count(_) -> Optional[int]:
        return None

    monkeypatch.setattr(repo, "count", mock_get_count)
    mocker.spy(repo, "count")
