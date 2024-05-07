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


# --- SEARCH


def test_search(event_repo_mock):
    result = event_service.search({"q": "two"})
    assert result is not None
    assert len(result) == 1
    assert event_repo_mock.search.call_count == 1


def test_search_db_error(event_repo_mock):
    event_repo_mock.throw_repository_error = True
    with pytest.raises(RepositoryError):
        event_service.search({"q": "error"})
    assert event_repo_mock.search.call_count == 1


def test_search_request_timeout(event_repo_mock):
    event_repo_mock.throw_timeout_error = True
    with pytest.raises(TimeoutError):
        event_service.search({"q": "timeout"})
    assert event_repo_mock.search.call_count == 1


def test_search_missing(event_repo_mock):
    event_repo_mock.return_empty = True
    result = event_service.search({"q": "empty"})
    assert result is not None
    assert len(result) == 0
    assert event_repo_mock.search.call_count == 1
