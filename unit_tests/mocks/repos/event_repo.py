from typing import Optional
from pytest import MonkeyPatch

from sqlalchemy import exc
from app.model.event import EventCreateDTO, EventReadDTO
from unit_tests.helpers.event import create_event_read_dto


def mock_event_repo(event_repo, monkeypatch: MonkeyPatch, mocker):
    event_repo.return_empty = False
    event_repo.throw_repository_error = False

    def maybe_throw():
        if event_repo.throw_repository_error:
            raise exc.SQLAlchemyError("bad repo")

    def mock_get_all(_) -> list[EventReadDTO]:
        values = []
        for x in range(3):
            dto = create_event_read_dto(import_id=f"id{x}")
            values.append(dto)
        return values

    def mock_get(_, import_id: str) -> Optional[EventReadDTO]:
        dto = create_event_read_dto(import_id)
        return dto

    def mock_search(_, q: str) -> list[EventReadDTO]:
        maybe_throw()
        if not event_repo.return_empty:
            return [create_event_read_dto("search1")]
        return []

    def mock_create(_, data: EventCreateDTO) -> str:
        maybe_throw()
        if event_repo.return_empty:
            raise exc.NoResultFound()
        return "test.new.event.0"

    def mock_get_count(_) -> Optional[int]:
        maybe_throw()
        if not event_repo.return_empty:
            return 5
        return

    monkeypatch.setattr(event_repo, "get", mock_get)
    mocker.spy(event_repo, "get")

    monkeypatch.setattr(event_repo, "all", mock_get_all)
    mocker.spy(event_repo, "all")

    monkeypatch.setattr(event_repo, "search", mock_search)
    mocker.spy(event_repo, "search")

    monkeypatch.setattr(event_repo, "create", mock_create)
    mocker.spy(event_repo, "create")

    monkeypatch.setattr(event_repo, "count", mock_get_count)
    mocker.spy(event_repo, "count")
