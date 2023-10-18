from typing import Optional
from pytest import MonkeyPatch
from app.errors import RepositoryError

from app.model.event import EventReadDTO
from unit_tests.helpers.event import create_event_read_dto


def mock_event_service(event_service, monkeypatch: MonkeyPatch, mocker):
    event_service.missing = False
    event_service.throw_repository_error = False

    def maybe_throw():
        if event_service.throw_repository_error:
            raise RepositoryError("bad repo")

    def mock_get_all_documents() -> list[EventReadDTO]:
        maybe_throw()
        return [create_event_read_dto("test")]

    def mock_get_document(import_id: str) -> Optional[EventReadDTO]:
        maybe_throw()
        if not event_service.missing:
            return create_event_read_dto(import_id)

    def mock_search_documents(q: str) -> list[EventReadDTO]:
        maybe_throw()
        if event_service.missing:
            return []
        else:
            return [create_event_read_dto("search1")]

    def mock_count_collection() -> Optional[int]:
        maybe_throw()
        if event_service.missing:
            return None
        return 33

    monkeypatch.setattr(event_service, "get", mock_get_document)
    mocker.spy(event_service, "get")

    monkeypatch.setattr(event_service, "all", mock_get_all_documents)
    mocker.spy(event_service, "all")

    monkeypatch.setattr(event_service, "search", mock_search_documents)
    mocker.spy(event_service, "search")

    monkeypatch.setattr(event_service, "count", mock_count_collection)
    mocker.spy(event_service, "count")
