"""
Tests the family service.

Uses a family repo mock and ensures that the repo is called.
"""

import pytest

import app.service.family as family_service
from app.errors import RepositoryError


def test_all_returns_families_if_exists(family_repo_mock, admin_user_context):
    result = family_service.all(admin_user_context)
    assert result is not None
    assert family_repo_mock.all.call_count == 1


def test_all_returns_empty_list_if_no_results(family_repo_mock, admin_user_context):
    family_repo_mock.return_empty = True
    result = family_service.all(admin_user_context)
    assert result == []
    assert family_repo_mock.all.call_count == 1


def test_all_raises_db_error(family_repo_mock, admin_user_context):
    family_repo_mock.throw_repository_error = True
    with pytest.raises(RepositoryError) as e:
        family_service.all(admin_user_context)
    expected_msg = "bad family repo"
    assert e.value.message == expected_msg
    assert family_repo_mock.all.call_count == 1
