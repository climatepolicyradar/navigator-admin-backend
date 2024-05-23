import pytest

import app.service.collection as collection_service
from app.errors import RepositoryError

USER_EMAIL = "test@cpr.org"
# --- COUNT


def test_count(collection_repo_mock, app_user_repo_mock):
    result = collection_service.count(USER_EMAIL)
    assert result is not None
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert app_user_repo_mock.is_superuser.call_count == 1
    assert collection_repo_mock.count.call_count == 1


def test_count_returns_none(collection_repo_mock, app_user_repo_mock):
    collection_repo_mock.return_empty = True
    result = collection_service.count(USER_EMAIL)
    assert result is None
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert app_user_repo_mock.is_superuser.call_count == 1
    assert collection_repo_mock.count.call_count == 1


def test_count_raises_if_db_error(collection_repo_mock, app_user_repo_mock):
    collection_repo_mock.throw_repository_error = True
    with pytest.raises(RepositoryError) as e:
        collection_service.count(USER_EMAIL)

    expected_msg = "bad collection repo"
    assert e.value.message == expected_msg
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert app_user_repo_mock.is_superuser.call_count == 1
    assert collection_repo_mock.count.call_count == 1
