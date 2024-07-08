import pytest

import app.service.event as event_service
from app.errors import ValidationError


def test_get(event_repo_mock):
    result = event_service.get("id.1.2.3")
    assert result is not None
    assert result.import_id == "id.1.2.3"
    assert event_repo_mock.get.call_count == 1


def test_get_returns_none(event_repo_mock):
    event_repo_mock.return_empty = True
    result = event_service.get("id.1.2.3")
    assert result is None
    assert event_repo_mock.get.call_count == 1


def test_get_raises_when_invalid_id(event_repo_mock):
    with pytest.raises(ValidationError) as e:
        event_service.get("a.b.c")
    expected_msg = "The import id a.b.c is invalid!"
    assert e.value.message == expected_msg
    assert event_repo_mock.get.call_count == 0
