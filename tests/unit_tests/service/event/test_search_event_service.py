import pytest

import app.service.event as event_service
from app.errors import RepositoryError


def test_search(event_repo_mock, admin_user_context):
    result = event_service.search({"q": "two"}, admin_user_context)
    assert result is not None
    assert len(result) == 1
    assert event_repo_mock.search.call_count == 1


def test_search_db_error(event_repo_mock, admin_user_context):
    event_repo_mock.throw_repository_error = True
    with pytest.raises(RepositoryError):
        event_service.search({"q": "error"}, admin_user_context)
    assert event_repo_mock.search.call_count == 1


def test_search_request_timeout(event_repo_mock, admin_user_context):
    event_repo_mock.throw_timeout_error = True
    with pytest.raises(TimeoutError):
        event_service.search({"q": "timeout"}, admin_user_context)
    assert event_repo_mock.search.call_count == 1


def test_search_missing(event_repo_mock, admin_user_context):
    event_repo_mock.return_empty = True
    result = event_service.search({"q": "empty"}, admin_user_context)
    assert result is not None
    assert len(result) == 0
    assert event_repo_mock.search.call_count == 1
