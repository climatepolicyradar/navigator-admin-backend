from typing import Optional

from pytest import MonkeyPatch
from sqlalchemy import exc

from app.errors import RepositoryError
from app.model.event import EventCreateDTO, EventReadDTO, EventWriteDTO
from tests.helpers.event import create_event_read_dto

ALTERNATIVE_ORG_ID = 999
STANDARD_ORG_ID = 1


def mock_event_repo(event_repo, monkeypatch: MonkeyPatch, mocker):
    event_repo.return_empty = False
    event_repo.throw_repository_error = False
    event_repo.throw_timeout_error = False
    event_repo.is_superuser = False
    event_repo.no_org = False
    event_repo.alternative_org = False

    def maybe_throw():
        if event_repo.throw_repository_error:
            raise RepositoryError("bad event repo")

    def maybe_timeout():
        if event_repo.throw_timeout_error:
            raise TimeoutError

    def mock_get_all(_, org_id: Optional[int]) -> list[EventReadDTO]:
        maybe_throw()
        if event_repo.return_empty:
            return []
        values = []
        for x in range(3):
            dto = create_event_read_dto(import_id=f"id{x}")
            values.append(dto)
        return values

    def mock_get(_, import_id: str) -> Optional[EventReadDTO]:
        dto = create_event_read_dto(import_id)
        return dto

    def mock_search(_, q: dict, org_id: Optional[int]) -> list[EventReadDTO]:
        maybe_throw()
        maybe_timeout()
        if not event_repo.return_empty:
            return [create_event_read_dto("search1")]
        return []

    def mock_create(_, data: EventCreateDTO) -> str:
        maybe_throw()
        if event_repo.return_empty:
            raise exc.NoResultFound()
        return "test.new.event.0"

    def mock_update(_, import_id: str, data: EventWriteDTO) -> EventReadDTO:
        maybe_throw()
        if event_repo.return_empty:
            raise exc.NoResultFound()
        return create_event_read_dto("a.b.c.d")

    def mock_delete(_, import_id: str) -> bool:
        maybe_throw()
        return not event_repo.return_empty

    def mock_get_count(_, org_id: Optional[int]) -> Optional[int]:
        maybe_throw()
        if not event_repo.return_empty:
            if event_repo.is_superuser:
                return 5
            return 2
        return

    def mock_get_org_from_import_id(_, import_id: str) -> Optional[int]:
        maybe_throw()
        if event_repo.no_org is True:
            return None

        if event_repo.alternative_org is True:
            return ALTERNATIVE_ORG_ID
        return STANDARD_ORG_ID

    monkeypatch.setattr(event_repo, "get", mock_get)
    mocker.spy(event_repo, "get")

    monkeypatch.setattr(event_repo, "all", mock_get_all)
    mocker.spy(event_repo, "all")

    monkeypatch.setattr(event_repo, "search", mock_search)
    mocker.spy(event_repo, "search")

    monkeypatch.setattr(event_repo, "create", mock_create)
    mocker.spy(event_repo, "create")

    monkeypatch.setattr(event_repo, "update", mock_update)
    mocker.spy(event_repo, "update")

    monkeypatch.setattr(event_repo, "delete", mock_delete)
    mocker.spy(event_repo, "delete")

    monkeypatch.setattr(event_repo, "count", mock_get_count)
    mocker.spy(event_repo, "count")

    monkeypatch.setattr(
        event_repo, "get_org_from_import_id", mock_get_org_from_import_id
    )
    mocker.spy(event_repo, "get_org_from_import_id")
