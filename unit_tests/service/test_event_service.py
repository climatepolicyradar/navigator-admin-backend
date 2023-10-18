import pytest
import app.service.event as event_service
from app.errors import RepositoryError, ValidationError
from unit_tests.helpers.event import create_event_create_dto

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
    result = event_service.search("two")
    assert result is not None
    assert len(result) == 1
    assert event_repo_mock.search.call_count == 1


def test_search_when_missing(event_repo_mock):
    event_repo_mock.return_empty = True
    result = event_service.search("empty")
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
