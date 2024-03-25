import pytest

import app.service.event as event_service
from app.errors import RepositoryError, ValidationError
from app.model.event import EventReadDTO, EventWriteDTO
from tests.unit_tests.helpers.event import create_event_create_dto


def _to_write_dto(dto: EventReadDTO) -> EventWriteDTO:
    return EventWriteDTO(
        event_title=dto.event_title,
        date=dto.date,
        event_type_value=dto.event_type_value,
    )


# --- GET


def test_get(event_repo_mock):
    result = event_service.get("id.1.2.3")
    assert result is not None
    assert result.import_id == "id.1.2.3"
    assert event_repo_mock.get.call_count == 1


def test_get_returns_none(event_repo_mock):
    event_repo_mock.return_empty = True
    result = event_service.get("id.1.2.3")
    assert result is not None
    assert event_repo_mock.get.call_count == 1


def test_get_raises_when_invalid_id(event_repo_mock):
    with pytest.raises(ValidationError) as e:
        event_service.get("a.b.c")
    expected_msg = "The import id a.b.c is invalid!"
    assert e.value.message == expected_msg
    assert event_repo_mock.get.call_count == 0


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


# --- CREATE


def test_create(event_repo_mock, family_repo_mock):
    new_event = create_event_create_dto()
    event = event_service.create(new_event)
    assert event is not None
    assert event_repo_mock.create.call_count == 1
    assert family_repo_mock.get.call_count == 1


def test_create_when_db_fails(event_repo_mock, family_repo_mock):
    new_event = create_event_create_dto()
    event_repo_mock.return_empty = True

    with pytest.raises(RepositoryError):
        event_service.create(new_event)
    assert event_repo_mock.create.call_count == 1
    assert family_repo_mock.get.call_count == 1


def test_create_raises_when_invalid_family_id(event_repo_mock):
    new_event = create_event_create_dto(family_import_id="invalid family")
    with pytest.raises(ValidationError) as e:
        event_service.create(new_event)
    expected_msg = f"The import id {new_event.family_import_id} is invalid!"
    assert e.value.message == expected_msg
    assert event_repo_mock.create.call_count == 0


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
