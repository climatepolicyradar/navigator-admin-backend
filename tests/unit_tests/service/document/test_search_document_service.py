import pytest

import app.service.document as doc_service
from app.errors import RepositoryError


def test_search(document_repo_mock, admin_user_context):
    result = doc_service.search({"q": "two"}, admin_user_context)
    assert result is not None
    assert len(result) == 1
    assert document_repo_mock.search.call_count == 1


def test_search_db_error(document_repo_mock, admin_user_context):
    document_repo_mock.throw_repository_error = True
    with pytest.raises(RepositoryError):
        doc_service.search({"q": "error"}, admin_user_context)
    assert document_repo_mock.search.call_count == 1


def test_search_request_timeout(document_repo_mock, admin_user_context):
    document_repo_mock.throw_timeout_error = True
    with pytest.raises(TimeoutError):
        doc_service.search({"q": "timeout"}, admin_user_context)
    assert document_repo_mock.search.call_count == 1


def test_search_missing(document_repo_mock, admin_user_context):
    document_repo_mock.return_empty = True
    result = doc_service.search({"q": "empty"}, admin_user_context)
    assert result is not None
    assert len(result) == 0
    assert document_repo_mock.search.call_count == 1
