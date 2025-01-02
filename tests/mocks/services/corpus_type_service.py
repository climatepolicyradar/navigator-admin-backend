from typing import Optional

from pytest import MonkeyPatch

from app.errors import RepositoryError
from app.model.corpus_type import CorpusTypeCreateDTO, CorpusTypeReadDTO


def mock_corpus_type_service(corpus_type_service, monkeypatch: MonkeyPatch, mocker):
    corpus_type_service.valid = True
    corpus_type_service.missing = False
    corpus_type_service.throw_repository_error = False

    def maybe_throw():
        if corpus_type_service.throw_repository_error:
            raise RepositoryError("bad repo")

    def mock_all(user_email: str) -> list[CorpusTypeReadDTO]:
        maybe_throw()
        return [
            CorpusTypeReadDTO(
                name=f"test_name_{x}", description=f"test_description_{x}", metadata={}
            )
            for x in range(2)
        ]

    def mock_get(name: str) -> Optional[CorpusTypeReadDTO]:
        maybe_throw()

        if not corpus_type_service.missing:
            return CorpusTypeReadDTO(
                name="test_name", description="test_description", metadata={}
            )
        return None

    def mock_create(data: CorpusTypeCreateDTO) -> str:
        maybe_throw()
        if corpus_type_service.missing:
            raise RepositoryError("missing")
        return "test_ct_name"

    monkeypatch.setattr(corpus_type_service, "all", mock_all)
    mocker.spy(corpus_type_service, "all")

    monkeypatch.setattr(corpus_type_service, "get", mock_get)
    mocker.spy(corpus_type_service, "create")

    monkeypatch.setattr(corpus_type_service, "create", mock_create)
    mocker.spy(corpus_type_service, "create")
