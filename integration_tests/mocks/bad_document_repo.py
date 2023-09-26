from typing import Optional
from pytest import MonkeyPatch
from app.errors import RepositoryError

from app.model.document import DocumentReadDTO


def mock_bad_document_repo(repo, monkeypatch: MonkeyPatch, mocker):
    def mock_get_all(_):
        raise RepositoryError("Bad Repo")

    def mock_get(_, import_id: str) -> Optional[DocumentReadDTO]:
        raise RepositoryError("Bad Repo")

    def mock_search(_, q: str) -> list[DocumentReadDTO]:
        raise RepositoryError("Bad Repo")

    def mock_update(_, data: DocumentReadDTO) -> Optional[DocumentReadDTO]:
        raise RepositoryError("Bad Repo")

    def mock_create(_, data: DocumentReadDTO) -> Optional[DocumentReadDTO]:
        raise RepositoryError("Bad Repo")

    def mock_delete(_, import_id: str) -> bool:
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
