from typing import Optional

from pytest import MonkeyPatch

from app.errors import AuthorisationError, RepositoryError, ValidationError
from app.model.event import EventCreateDTO, EventReadDTO, EventWriteDTO
from app.model.user import UserContext
from tests.helpers.event import create_event_read_dto


def mock_event_service(event_service, monkeypatch: MonkeyPatch, mocker):
    event_service.missing = False
    event_service.throw_repository_error = False
    event_service.throw_timeout_error = False
    event_service.throw_validation_error = False
    event_service.org_mismatch = False
    event_service.superuser = False

    def maybe_throw():
        if event_service.throw_repository_error:
            raise RepositoryError("bad repo")
        if event_service.throw_validation_error:
            raise ValidationError("Validation error")

    def maybe_timeout():
        if event_service.throw_timeout_error:
            raise TimeoutError

    def mock_get_all_events(user_email: str) -> list[EventReadDTO]:
        maybe_throw()
        return [create_event_read_dto("test")]

    def mock_get_event(import_id: str) -> Optional[EventReadDTO]:
        maybe_throw()
        if not event_service.missing:
            return create_event_read_dto(import_id)

    def mock_search_events(q: dict, user_email: str) -> list[EventReadDTO]:
        maybe_throw()
        maybe_timeout()
        if event_service.missing:
            return []
        else:
            return [create_event_read_dto("search1")]

    def mock_create_event(data: EventCreateDTO, user: UserContext) -> str:
        maybe_throw()
        if event_service.org_mismatch and not event_service.superuser:
            raise AuthorisationError("Org mismatch")

        if event_service.missing:
            raise ValidationError(f"Could not find family for {data.family_import_id}")

        return "new.event.id.0"

    def mock_update_event(
        import_id: str, data: EventWriteDTO, user: UserContext
    ) -> Optional[EventReadDTO]:
        maybe_throw()
        if event_service.throw_validation_error:
            raise ValidationError("Validation error")

        if event_service.org_mismatch and not event_service.superuser:
            raise AuthorisationError("Org mismatch")

        if not event_service.missing:
            return create_event_read_dto(
                import_id, "family_import_id", data.event_title
            )

    def mock_delete_event(_, user: UserContext) -> bool:
        maybe_throw()
        if event_service.org_mismatch and not event_service.superuser:
            raise AuthorisationError("Org mismatch")
        if event_service.throw_validation_error:
            raise ValidationError("No org")
        return not event_service.missing

    monkeypatch.setattr(event_service, "get", mock_get_event)
    mocker.spy(event_service, "get")

    monkeypatch.setattr(event_service, "all", mock_get_all_events)
    mocker.spy(event_service, "all")

    monkeypatch.setattr(event_service, "search", mock_search_events)
    mocker.spy(event_service, "search")

    monkeypatch.setattr(event_service, "create", mock_create_event)
    mocker.spy(event_service, "create")

    monkeypatch.setattr(event_service, "update", mock_update_event)
    mocker.spy(event_service, "update")

    monkeypatch.setattr(event_service, "delete", mock_delete_event)
    mocker.spy(event_service, "delete")
