"""
Tests the family service.

Uses a family repo mock and ensures that the repo is called.
"""

import pytest

import app.service.family as family_service
from app.errors import RepositoryError

USER_EMAIL = "test@cpr.org"
ORG_ID = 1

# --- COUNT


def test_count(family_repo_mock):
    result = family_service.count()
    assert result is not None
    assert family_repo_mock.count.call_count == 1


def test_count_returns_none(family_repo_mock):
    family_repo_mock.return_empty = True
    result = family_service.count()
    assert result is None
    assert family_repo_mock.count.call_count == 1


def test_count_raises_if_db_error(family_repo_mock):
    family_repo_mock.throw_repository_error = True
    with pytest.raises(RepositoryError) as e:
        family_service.count()

    expected_msg = "bad repo"
    assert e.value.message == expected_msg
    assert family_repo_mock.count.call_count == 1
