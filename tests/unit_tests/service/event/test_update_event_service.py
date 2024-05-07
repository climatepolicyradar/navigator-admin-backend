import pytest

import app.service.event as event_service
from app.errors import RepositoryError, ValidationError
from app.model.event import EventReadDTO, EventWriteDTO


def _to_write_dto(dto: EventReadDTO) -> EventWriteDTO:
    return EventWriteDTO(
        event_title=dto.event_title,
        date=dto.date,
        event_type_value=dto.event_type_value,
    )


# --- UPDATE


def test_update(
    event_repo_mock,
):
    event = event_service.get("a.b.c.d")
    assert event is not None

    result = event_service.update(event.import_id, _to_write_dto(event))
    assert result is not None
    assert event_repo_mock.update.call_count == 1


def test_update_when_missing(
    event_repo_mock,
):
    event = event_service.get("a.b.c.d")
    assert event is not None
    event_repo_mock.return_empty = True

    with pytest.raises(RepositoryError) as e:
        event_service.update(event.import_id, _to_write_dto(event))
    assert e.value.message == "Error when updating event a.b.c.d"
    assert event_repo_mock.update.call_count == 1


def test_update_raises_when_invalid_id(
    event_repo_mock,
):
    event = event_service.get("a.b.c.d")
    assert event is not None  # needed to placate pyright
    event.import_id = "invalid"

    with pytest.raises(ValidationError) as e:
        event_service.update(event.import_id, _to_write_dto(event))
    expected_msg = f"The import id {event.import_id} is invalid!"
    assert e.value.message == expected_msg
    assert event_repo_mock.update.call_count == 0
