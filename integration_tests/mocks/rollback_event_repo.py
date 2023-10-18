from typing import Optional
from pytest import MonkeyPatch

from sqlalchemy.exc import NoResultFound

from app.model.event import EventCreateDTO, EventReadDTO


def mock_rollback_event_repo(event_repo, monkeypatch: MonkeyPatch, mocker):
    actual_create = event_repo.create

    def mock_create_document(db, data: EventCreateDTO) -> Optional[EventReadDTO]:
        actual_create(db, data)
        raise NoResultFound()

    monkeypatch.setattr(event_repo, "create", mock_create_document)
    mocker.spy(event_repo, "create")
