from typing import Optional

from pytest import MonkeyPatch
from sqlalchemy.exc import NoResultFound

from app.model.corpus import CorpusCreateDTO, CorpusReadDTO, CorpusWriteDTO


def mock_rollback_corpus_repo(corpus_repo, monkeypatch: MonkeyPatch, mocker):
    actual_update = corpus_repo.update
    actual_create = corpus_repo.create

    def mock_update_corpus(
        db, import_id: str, data: CorpusWriteDTO
    ) -> Optional[CorpusReadDTO]:
        actual_update(db, import_id, data)
        raise NoResultFound()

    def mock_create_corpus(db, data: CorpusCreateDTO) -> str:
        actual_create(db, data)
        raise NoResultFound()

    monkeypatch.setattr(corpus_repo, "update", mock_update_corpus)
    mocker.spy(corpus_repo, "update")

    monkeypatch.setattr(corpus_repo, "create", mock_create_corpus)
    mocker.spy(corpus_repo, "create")
