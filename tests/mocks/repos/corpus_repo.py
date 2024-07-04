from typing import Optional, cast

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

    def mock_get_taxonomy_from_corpus(_, __, ___=None) -> Optional[TaxonomyData]:
        if corpus_repo.bad_taxonomy:
            return None

        color = {
            "allow_blanks": False,
            "allow_any": False,
            "allowed_values": ["pink", "blue"],
        }
        size = {"allow_blanks": True, "allow_any": True, "allowed_values": []}
        return cast(TaxonomyData, {"color": color, "size": size})

    monkeypatch.setattr(corpus_repo, "get_corpus_org_id", mock_get_corpus_org_id)
    mocker.spy(corpus_repo, "get_corpus_org_id")

    monkeypatch.setattr(corpus_repo, "validate", mock_validate)
    mocker.spy(corpus_repo, "validate")

    monkeypatch.setattr(
        corpus_repo, "get_taxonomy_from_corpus", mock_get_taxonomy_from_corpus
    )
    mocker.spy(corpus_repo, "get_taxonomy_from_corpus")
