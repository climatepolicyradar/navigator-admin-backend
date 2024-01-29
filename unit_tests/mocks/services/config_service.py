from pytest import MonkeyPatch
from app.clients.db.errors import RepositoryError

from app.model.config import ConfigReadDTO, DocumentConfig, EventConfig


def mock_config_service(config_service, monkeypatch: MonkeyPatch, mocker):
    config_service.throw_repository_error = False

    def maybe_throw():
        if config_service.throw_repository_error:
            raise RepositoryError("bad repo")

    def mock_get_config() -> ConfigReadDTO:
        maybe_throw()
        return ConfigReadDTO(
            geographies=[],
            taxonomies={},
            languages={},
            document=DocumentConfig(roles=[], types=[], variants=[]),
            event=EventConfig(types=[]),
        )

    monkeypatch.setattr(config_service, "get", mock_get_config)
    mocker.spy(config_service, "get")
