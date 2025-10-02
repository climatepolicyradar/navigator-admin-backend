"""
Tests the family service.

Uses a family repo mock and ensures that the repo is called.
"""

import pytest

import app.service.family as family_service
from app.errors import RepositoryError


def test_search(family_repo_mock, admin_user_context):
    result = family_service.search({"q": "two"}, admin_user_context)
    assert result is not None
    assert len(result) == 2
    assert family_repo_mock.search.call_count == 1


def test_search_on_specific_field(family_repo_mock, admin_user_context):
    result = family_service.search({"title": "one"}, admin_user_context)
    assert result is not None
    assert len(result) == 1
    assert family_repo_mock.search.call_count == 1


def test_search_db_error(family_repo_mock, admin_user_context):
    family_repo_mock.throw_repository_error = True
    with pytest.raises(RepositoryError):
        family_service.search({"q": "error"}, admin_user_context)
    assert family_repo_mock.search.call_count == 1


def test_search_request_timeout(family_repo_mock, admin_user_context):
    family_repo_mock.throw_timeout_error = True
    with pytest.raises(TimeoutError):
        family_service.search({"q": "timeout"}, admin_user_context)
    assert family_repo_mock.search.call_count == 1


def test_search_missing(family_repo_mock, admin_user_context):
    family_repo_mock.return_empty = True
    result = family_service.search({"q": "empty"}, admin_user_context)
    assert result is not None
    assert len(result) == 0
    assert family_repo_mock.search.call_count == 1


def test_search_with_corpus_filter(family_repo_mock, admin_user_context):
    """Test that corpus filtering parameter is passed correctly to the repository."""
    result = family_service.search(
        {"q": "test"}, admin_user_context, geography=None, corpus=["corpus1", "corpus2"]
    )
    assert result is not None
    assert family_repo_mock.search.call_count == 1

    # Verify the repository was called with the correct parameters
    call_args = family_repo_mock.search.call_args
    assert call_args[0][0] is not None  # db session
    assert call_args[0][1] == {"q": "test"}  # search_params
    assert call_args[0][2] is not None  # org_id
    assert call_args[0][3] is None  # geography
    assert call_args[0][4] == ["corpus1", "corpus2"]  # corpus


def test_search_with_geography_and_corpus_filters(family_repo_mock, admin_user_context):
    """Test that both geography and corpus filtering work together."""
    result = family_service.search(
        {"q": "test"},
        admin_user_context,
        geography=["USA", "CAN"],
        corpus=["corpus1", "corpus2"],
    )
    assert result is not None
    assert family_repo_mock.search.call_count == 1

    # Verify the repository was called with the correct parameters
    call_args = family_repo_mock.search.call_args
    assert call_args[0][0] is not None  # db session
    assert call_args[0][1] == {"q": "test"}  # search_params
    assert call_args[0][2] is not None  # org_id
    assert call_args[0][3] == ["USA", "CAN"]  # geography
    assert call_args[0][4] == ["corpus1", "corpus2"]  # corpus
