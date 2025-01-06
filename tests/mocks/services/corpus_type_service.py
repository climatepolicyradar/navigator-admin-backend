from typing import Optional

from pytest import MonkeyPatch

from app.errors import RepositoryError, ValidationError
from app.model.corpus_type import CorpusTypeCreateDTO, CorpusTypeReadDTO


def mock_corpus_type_service(corpus_type_service, monkeypatch: MonkeyPatch, mocker):
    """Mock the corpus type service.

    :param corpus_type_service: The service to mock
    :param MonkeyPatch monkeypatch: pytest's MonkeyPatch fixture
    :param mocker: pytest's mocker fixture
    """
    corpus_type_service.valid = True
    corpus_type_service.missing = False
    corpus_type_service.throw_repository_error = False
    corpus_type_service.throw_validation_error = False

    def maybe_throw():
        if corpus_type_service.throw_repository_error:
            raise RepositoryError("bad repo")
        if corpus_type_service.throw_validation_error:
            raise ValidationError("Validation error")

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
        return data.name if data.name else "test_ct_name"

    monkeypatch.setattr(corpus_type_service, "all", mock_all)
    monkeypatch.setattr(corpus_type_service, "get", mock_get)
    monkeypatch.setattr(corpus_type_service, "create", mock_create)

    mocker.spy(corpus_type_service, "all")
    mocker.spy(corpus_type_service, "get")
    mocker.spy(corpus_type_service, "create")
