"""
Tests the family service.

Uses a family repo mock and ensures that the repo is called.
"""

import pytest

import app.service.family as family_service
from app.errors import RepositoryError

USER_EMAIL = "test@cpr.org"

# --- COUNT


def test_count(family_repo_mock, app_user_repo_mock):
    result = family_service.count(USER_EMAIL)
    assert result is not None
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert app_user_repo_mock.is_superuser.call_count == 1
    assert family_repo_mock.count.call_count == 1


def test_count_returns_none(family_repo_mock, app_user_repo_mock):
    family_repo_mock.return_empty = True
    result = family_service.count(USER_EMAIL)
    assert result is None
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert app_user_repo_mock.is_superuser.call_count == 1
    assert family_repo_mock.count.call_count == 1


def test_count_raises_if_db_error(family_repo_mock, app_user_repo_mock):
    family_repo_mock.throw_repository_error = True
    with pytest.raises(RepositoryError) as e:
        family_service.count(USER_EMAIL)

    expected_msg = "bad family repo"
    assert e.value.message == expected_msg
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert app_user_repo_mock.is_superuser.call_count == 1
    assert family_repo_mock.count.call_count == 1
