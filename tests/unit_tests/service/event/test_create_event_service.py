import pytest

import app.service.event as event_service
from app.errors import RepositoryError, ValidationError
from tests.helpers.event import create_event_create_dto

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
