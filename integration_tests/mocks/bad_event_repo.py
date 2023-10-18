from typing import Optional
from pytest import MonkeyPatch
from app.errors import RepositoryError

from app.model.event import EventReadDTO


def mock_bad_event_repo(repo, monkeypatch: MonkeyPatch, mocker):
    def mock_get_all(_):
        raise RepositoryError("Bad Repo")

    def mock_get(_, import_id: str) -> Optional[EventReadDTO]:
        raise RepositoryError("Bad Repo")

    def mock_search(_, q: str) -> list[EventReadDTO]:
        raise RepositoryError("Bad Repo")

    def mock_get_count(_) -> Optional[int]:
        raise RepositoryError("Bad Repo")

    monkeypatch.setattr(repo, "get", mock_get)
    mocker.spy(repo, "get")

    monkeypatch.setattr(repo, "all", mock_get_all)
    mocker.spy(repo, "all")

    monkeypatch.setattr(repo, "search", mock_search)
    mocker.spy(repo, "search")

    monkeypatch.setattr(repo, "count", mock_get_count)
    mocker.spy(repo, "count")


def mock_event_count_none(repo, monkeypatch: MonkeyPatch, mocker):
    def mock_get_count(_) -> Optional[int]:
        return None

    monkeypatch.setattr(repo, "count", mock_get_count)
    mocker.spy(repo, "count")
