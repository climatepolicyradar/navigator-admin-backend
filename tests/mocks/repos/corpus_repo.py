from typing import Optional

from pytest import MonkeyPatch


def mock_corpus_repo(corpus_repo, monkeypatch: MonkeyPatch, mocker):
    corpus_repo.error = False
    corpus_repo.valid = True

    def mock_get_corpus_org_id(_, __) -> Optional[int]:
        if not corpus_repo.error:
            return 1

    def mock_validate(_, __) -> bool:
        return corpus_repo.valid

    monkeypatch.setattr(corpus_repo, "get_corpus_org_id", mock_get_corpus_org_id)
    mocker.spy(corpus_repo, "get_corpus_org_id")

    monkeypatch.setattr(corpus_repo, "validate", mock_validate)
    mocker.spy(corpus_repo, "validate")
