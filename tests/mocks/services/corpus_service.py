from pydantic import AnyHttpUrl
from pytest import MonkeyPatch

from app.errors import AuthorisationError, RepositoryError, ValidationError
from app.model.corpus import CorpusLogoUploadDTO


def mock_corpus_service(corpus_service, monkeypatch: MonkeyPatch, mocker):
    corpus_service.valid = True
    corpus_service.org_mismatch = False
    corpus_service.throw_repository_error = False
    corpus_service.invalid_corpus_id = False

    def maybe_throw():
        if corpus_service.throw_repository_error:
            raise RepositoryError("bad repo")

    def mock_validate():
        maybe_throw()
        return corpus_service.valid

    def mock_get_corpus_org_id(_):
        if corpus_service.org_mismatch:
            raise AuthorisationError("Org mismatch")
        return 1

    def mock_get_upload_url(corpus_id: str) -> CorpusLogoUploadDTO:
        if corpus_service.invalid_corpus_id:
            raise ValidationError("Corpus not found")
        return CorpusLogoUploadDTO(
            presigned_upload_url=AnyHttpUrl(
                "https://test-bucket.s3.amazonaws.com/test-key"
            ),
            object_cdn_url=AnyHttpUrl("https://cdn.test.com/test-key"),
        )

    monkeypatch.setattr(corpus_service, "validate", mock_validate)
    mocker.spy(corpus_service, "validate")

    monkeypatch.setattr(corpus_service, "get_corpus_org_id", mock_get_corpus_org_id)
    mocker.spy(corpus_service, "get_corpus_org_id")

    monkeypatch.setattr(corpus_service, "get_upload_url", mock_get_upload_url)
    mocker.spy(corpus_service, "get_upload_url")
