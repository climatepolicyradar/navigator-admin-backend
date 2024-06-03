"""
Tests the family service.

Uses a family repo mock and ensures that the repo is called.
"""

import pytest

import app.service.family as family_service
from app.errors import RepositoryError

USER_EMAIL = "test@cpr.org"
ORG_ID = 1


# --- SEARCH


def test_search(family_repo_mock, app_user_repo_mock):
    result = family_service.search({"q": "two"}, USER_EMAIL)
    assert result is not None
    assert len(result) == 2
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert app_user_repo_mock.is_superuser.call_count == 1
    assert family_repo_mock.search.call_count == 1


def test_search_on_specific_field(family_repo_mock, app_user_repo_mock):
    result = family_service.search({"title": "one"}, USER_EMAIL)
    assert result is not None
    assert len(result) == 1
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert app_user_repo_mock.is_superuser.call_count == 1
    assert family_repo_mock.search.call_count == 1


def test_search_db_error(family_repo_mock, app_user_repo_mock):
    family_repo_mock.throw_repository_error = True
    with pytest.raises(RepositoryError):
        family_service.search({"q": "error"}, USER_EMAIL)
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert app_user_repo_mock.is_superuser.call_count == 1
    assert family_repo_mock.search.call_count == 1


def test_search_request_timeout(family_repo_mock, app_user_repo_mock):
    family_repo_mock.throw_timeout_error = True
    with pytest.raises(TimeoutError):
        family_service.search({"q": "timeout"}, USER_EMAIL)
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert app_user_repo_mock.is_superuser.call_count == 1
    assert family_repo_mock.search.call_count == 1


def test_search_missing(family_repo_mock, app_user_repo_mock):
    family_repo_mock.return_empty = True
    result = family_service.search({"q": "empty"}, USER_EMAIL)
    assert result is not None
    assert len(result) == 0
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert app_user_repo_mock.is_superuser.call_count == 1
    assert family_repo_mock.search.call_count == 1
