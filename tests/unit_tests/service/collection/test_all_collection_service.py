import pytest

import app.service.collection as collection_service
from app.errors import RepositoryError

USER_EMAIL = "test@cpr.org"
# --- ALL


def test_all(collection_repo_mock, app_user_repo_mock):
    result = collection_service.all(USER_EMAIL)
    assert result is not None
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert app_user_repo_mock.is_superuser.call_count == 1
    assert collection_repo_mock.all.call_count == 1


def test_all_returns_empty_list_if_no_results(collection_repo_mock, app_user_repo_mock):
    collection_repo_mock.return_empty = True
    result = collection_service.all(USER_EMAIL)
    assert result == []
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert app_user_repo_mock.is_superuser.call_count == 1
    assert collection_repo_mock.all.call_count == 1


def test_all_raises_db_error(collection_repo_mock, app_user_repo_mock):
    collection_repo_mock.throw_repository_error = True
    with pytest.raises(RepositoryError) as e:
        collection_service.all("a.b.c")
    expected_msg = "bad collection repo"
    assert e.value.message == expected_msg
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert app_user_repo_mock.is_superuser.call_count == 1
    assert collection_repo_mock.all.call_count == 1
