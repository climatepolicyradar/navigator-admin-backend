from typing import Optional

from pytest import MonkeyPatch
from sqlalchemy import exc

from app.model.config import ConfigReadDTO, DocumentConfig


def mock_config_repo(config_repo, monkeypatch: MonkeyPatch, mocker):
    config_repo.return_empty = False
    config_repo.throw_repository_error = False

    def maybe_throw():
        if config_repo.throw_repository_error:
            raise exc.SQLAlchemyError("")

    def mock_get(_) -> Optional[ConfigReadDTO]:
        maybe_throw()
        return ConfigReadDTO(
            geographies=[],
            corpora=[],
            corpus_types=[],
            languages={},
            document=DocumentConfig(variants=[]),
        )

    monkeypatch.setattr(config_repo, "get", mock_get)
    mocker.spy(config_repo, "get")
