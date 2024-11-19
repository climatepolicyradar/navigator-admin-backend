from typing import Optional

from pytest import MonkeyPatch

from app.errors import RepositoryError
from app.model.corpus import CorpusCreateDTO, CorpusReadDTO, CorpusWriteDTO


def mock_bad_corpus_repo(repo, monkeypatch: MonkeyPatch, mocker):
    def mock_get_all(_):
        raise RepositoryError("Bad Repo")

    def mock_get(_, import_id: str) -> Optional[CorpusReadDTO]:
        raise RepositoryError("Bad Repo")

    def mock_search(_, q: str, org_id: Optional[int]) -> list[CorpusReadDTO]:
        raise RepositoryError("Bad Repo")

    def mock_update(_, import_id: str, data: CorpusWriteDTO) -> Optional[CorpusReadDTO]:
        raise RepositoryError("Bad Repo")

    def mock_create(_, data: CorpusCreateDTO) -> str:
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
