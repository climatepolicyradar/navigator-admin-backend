import pytest

import app.service.event as event_service
from app.errors import RepositoryError


def test_all(event_repo_mock, admin_user_context):
    result = event_service.all(admin_user_context)
    assert result is not None
    assert event_repo_mock.all.call_count == 1


def test_all__empty_list_if_no_results(event_repo_mock, admin_user_context):
    event_repo_mock.return_empty = True
    result = event_service.all(admin_user_context)
    assert result == []
    assert event_repo_mock.all.call_count == 1


def test_all_raises_db_error(event_repo_mock, admin_user_context):
    event_repo_mock.throw_repository_error = True
    with pytest.raises(RepositoryError) as e:
        event_service.all(admin_user_context)
    expected_msg = "bad event repo"
    assert e.value.message == expected_msg
    assert event_repo_mock.all.call_count == 1
