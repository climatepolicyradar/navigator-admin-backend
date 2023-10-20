from typing import Optional
from pytest import MonkeyPatch

from sqlalchemy.exc import NoResultFound

from app.model.event import EventCreateDTO, EventReadDTO, EventWriteDTO


def mock_rollback_event_repo(event_repo, monkeypatch: MonkeyPatch, mocker):
    actual_create = event_repo.create
    actual_update = event_repo.update

    def mock_create_event(db, data: EventCreateDTO) -> Optional[EventReadDTO]:
        actual_create(db, data)
        raise NoResultFound()

    def mock_update_event(db, import_id: str, data: EventWriteDTO) -> EventReadDTO:
        actual_update(db, import_id, data)
        raise NoResultFound()

    monkeypatch.setattr(event_repo, "create", mock_create_event)
    mocker.spy(event_repo, "create")

    monkeypatch.setattr(event_repo, "update", mock_update_event)
    mocker.spy(event_repo, "update")
