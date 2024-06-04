import pytest

import app.service.document as doc_service
from app.errors import RepositoryError

USER_EMAIL = "test@cpr.org"
# --- ALL


def test_all(document_repo_mock, app_user_repo_mock):
    result = doc_service.all(USER_EMAIL)
    assert result is not None
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert app_user_repo_mock.is_superuser.call_count == 1
    assert document_repo_mock.all.call_count == 1


def test_all_returns_empty_list_if_no_results(document_repo_mock, app_user_repo_mock):
    document_repo_mock.return_empty = True
    result = doc_service.all(USER_EMAIL)
    assert result == []
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert app_user_repo_mock.is_superuser.call_count == 1
    assert document_repo_mock.all.call_count == 1


def test_all_raises_db_error(document_repo_mock, app_user_repo_mock):
    document_repo_mock.throw_repository_error = True
    with pytest.raises(RepositoryError) as e:
        doc_service.all(USER_EMAIL)
    expected_msg = "bad document repo"
    assert e.value.message == expected_msg
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert app_user_repo_mock.is_superuser.call_count == 1
    assert document_repo_mock.all.call_count == 1
