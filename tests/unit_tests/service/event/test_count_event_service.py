import pytest

import app.service.event as event_service
from app.errors import RepositoryError
from app.model.event import EventReadDTO, EventWriteDTO


def _to_write_dto(dto: EventReadDTO) -> EventWriteDTO:
    return EventWriteDTO(
        event_title=dto.event_title,
        date=dto.date,
        event_type_value=dto.event_type_value,
    )


# --- COUNT


def test_count(event_repo_mock):
    result = event_service.count()
    assert result is not None
    assert event_repo_mock.count.call_count == 1


def test_count_returns_none(event_repo_mock):
    event_repo_mock.return_empty = True
    result = event_service.count()
    assert result is None
    assert event_repo_mock.count.call_count == 1


def test_count_raises_if_db_error(event_repo_mock):
    event_repo_mock.throw_repository_error = True
    with pytest.raises(RepositoryError) as e:
        event_service.count()

    expected_msg = "bad repo"
    assert e.value.message == expected_msg
    assert event_repo_mock.count.call_count == 1
