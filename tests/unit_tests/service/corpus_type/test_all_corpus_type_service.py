import pytest

import app.service.corpus_type as corpus_type_service
from app.errors import RepositoryError


def test_all(corpus_type_repo_mock, admin_user_context):
    result = corpus_type_service.all(admin_user_context)
    assert result is not None
    assert corpus_type_repo_mock.all.call_count == 1


def test_all_returns_empty_list_if_no_results(
    corpus_type_repo_mock, admin_user_context
):
    corpus_type_repo_mock.return_empty = True
    result = corpus_type_service.all(admin_user_context)
    assert result == []
    assert corpus_type_repo_mock.all.call_count == 1


def test_all_raises_db_error(corpus_type_repo_mock, bad_user_context):
    corpus_type_repo_mock.throw_repository_error = True
    with pytest.raises(RepositoryError) as e:
        corpus_type_service.all(bad_user_context)
    expected_msg = "bad corpus type repo"
    assert e.value.message == expected_msg
    assert corpus_type_repo_mock.all.call_count == 1
