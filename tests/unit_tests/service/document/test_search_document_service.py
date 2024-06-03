import pytest

import app.service.document as doc_service
from app.errors import RepositoryError

USER_EMAIL = "test@cpr.org"
# --- SEARCH


def test_search(document_repo_mock, app_user_repo_mock):
    result = doc_service.search({"q": "two"}, USER_EMAIL)
    assert result is not None
    assert len(result) == 1
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert app_user_repo_mock.is_superuser.call_count == 1
    assert document_repo_mock.search.call_count == 1


def test_search_db_error(document_repo_mock, app_user_repo_mock):
    document_repo_mock.throw_repository_error = True
    with pytest.raises(RepositoryError):
        doc_service.search({"q": "error"}, USER_EMAIL)
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert app_user_repo_mock.is_superuser.call_count == 1
    assert document_repo_mock.search.call_count == 1


def test_search_request_timeout(document_repo_mock, app_user_repo_mock):
    document_repo_mock.throw_timeout_error = True
    with pytest.raises(TimeoutError):
        doc_service.search({"q": "timeout"}, USER_EMAIL)
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert app_user_repo_mock.is_superuser.call_count == 1
    assert document_repo_mock.search.call_count == 1


def test_search_missing(document_repo_mock, app_user_repo_mock):
    document_repo_mock.return_empty = True
    result = doc_service.search({"q": "empty"}, USER_EMAIL)
    assert result is not None
    assert len(result) == 0
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert app_user_repo_mock.is_superuser.call_count == 1
    assert document_repo_mock.search.call_count == 1
