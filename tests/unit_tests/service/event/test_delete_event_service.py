import pytest

import app.service.event as event_service
from app.errors import ValidationError
from app.model.event import EventReadDTO, EventWriteDTO


def _to_write_dto(dto: EventReadDTO) -> EventWriteDTO:
    return EventWriteDTO(
        event_title=dto.event_title,
        date=dto.date,
        event_type_value=dto.event_type_value,
    )


# --- DELETE


def test_delete(event_repo_mock):
    ok = event_service.delete("a.b.c.d")
    assert ok
    assert event_repo_mock.delete.call_count == 1


def test_delete_when_missing(event_repo_mock):
    event_repo_mock.return_empty = True
    ok = event_service.delete("a.b.c.d")
    assert not ok
    assert event_repo_mock.delete.call_count == 1


def test_delete_raises_when_invalid_id(event_repo_mock):
    import_id = "invalid"
    with pytest.raises(ValidationError) as e:
        event_service.delete(import_id)
    expected_msg = f"The import id {import_id} is invalid!"
    assert e.value.message == expected_msg
    assert event_repo_mock.delete.call_count == 0
