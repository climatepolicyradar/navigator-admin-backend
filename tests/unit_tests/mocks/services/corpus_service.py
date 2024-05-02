from pytest import MonkeyPatch

from app.errors import AuthorisationError, RepositoryError


def mock_corpus_service(corpus_service, monkeypatch: MonkeyPatch, mocker):
    corpus_service.valid = True
    corpus_service.org_mismatch = False
    corpus_service.throw_repository_error = False

    def maybe_throw():
        if corpus_service.throw_repository_error:
            raise RepositoryError("bad repo")

    def mock_validate():
        maybe_throw()
        return corpus_service.valid

    def mock_get_corpus_org_id():
        if corpus_service.org_mismatch:
            raise AuthorisationError("Org mismatch between corpus and user")

    monkeypatch.setattr(corpus_service, "validate", mock_validate)
    mocker.spy(corpus_service, "validate")

    monkeypatch.setattr(corpus_service, "get_corpus_org_id", mock_get_corpus_org_id)
    mocker.spy(corpus_service, "get_corpus_org_id")
