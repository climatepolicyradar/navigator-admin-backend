from typing import Optional

from pytest import MonkeyPatch

from app.errors import RepositoryError
from app.model.corpus_type import CorpusTypeReadDTO


def mock_corpus_type_repo(corpus_type_repo, monkeypatch: MonkeyPatch, mocker):
    corpus_type_repo.valid = True
    corpus_type_repo.return_empty = False
    corpus_type_repo.throw_repository_error = False

    def maybe_throw():
        if corpus_type_repo.throw_repository_error:
            raise RepositoryError("bad corpus type repo")

    def mock_all(_, org_id: Optional[int]) -> list[CorpusTypeReadDTO]:
        maybe_throw()
        if corpus_type_repo.return_empty:
            return []
        return [
            CorpusTypeReadDTO(
                name=f"test_name_{x}", description=f"test_description_{x}", metadata={}
            )
            for x in range(2)
        ]

    def mock_get(_, name: str) -> Optional[CorpusTypeReadDTO]:
        maybe_throw()

        if not corpus_type_repo.return_empty:
            return CorpusTypeReadDTO(
                name="test_name", description="test_description", metadata={}
            )
        return None

    monkeypatch.setattr(corpus_type_repo, "all", mock_all)
    mocker.spy(corpus_type_repo, "all")

    monkeypatch.setattr(corpus_type_repo, "get", mock_get)
    mocker.spy(corpus_type_repo, "get")
