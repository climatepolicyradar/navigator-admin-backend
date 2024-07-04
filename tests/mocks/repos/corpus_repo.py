from typing import Optional

from pytest import MonkeyPatch

from app.model.config import TaxonomyData


def mock_corpus_repo(corpus_repo, monkeypatch: MonkeyPatch, mocker):
    corpus_repo.error = False
    corpus_repo.valid = True
    corpus_repo.bad_taxonomy = False

    def mock_get_corpus_org_id(_, __) -> Optional[int]:
        if not corpus_repo.error:
            return 1

    def mock_validate(_, __) -> bool:
        return corpus_repo.valid

    def mock_get_taxonomy_from_corpus(_, __) -> Optional[TaxonomyData]:
        if corpus_repo.bad_taxonomy:
            return None
        color = {"allow_blanks": True, "allow_any": True, "allowed_values": []}
        size = {"allow_blanks": True, "allow_any": True, "allowed_values": []}
        return {"color": color, "size": size}

    monkeypatch.setattr(corpus_repo, "get_corpus_org_id", mock_get_corpus_org_id)
    mocker.spy(corpus_repo, "get_corpus_org_id")

    monkeypatch.setattr(corpus_repo, "verify_corpus_exists", mock_validate)
    mocker.spy(corpus_repo, "verify_corpus_exists")

    monkeypatch.setattr(
        corpus_repo, "get_taxonomy_from_corpus", mock_get_taxonomy_from_corpus
    )
    mocker.spy(corpus_repo, "get_taxonomy_from_corpus")
