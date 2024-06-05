import pytest

import app.service.document as doc_service
from app.errors import AuthorisationError, RepositoryError, ValidationError

USER_EMAIL = "test@cpr.org"


def test_delete(document_repo_mock, app_user_repo_mock):
    ok = doc_service.delete("a.b.c.d", USER_EMAIL)
    assert ok
    assert document_repo_mock.get.call_count == 1
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert app_user_repo_mock.is_superuser.call_count == 1
    assert document_repo_mock.get_org_from_import_id.call_count == 1
    assert document_repo_mock.delete.call_count == 1


def test_delete_raises_when_invalid_id(document_repo_mock, app_user_repo_mock):
    import_id = "invalid"
    with pytest.raises(ValidationError) as e:
        doc_service.delete(import_id, USER_EMAIL)
    expected_msg = f"The import id {import_id} is invalid!"
    assert e.value.message == expected_msg
    assert document_repo_mock.get.call_count == 0
    assert app_user_repo_mock.get_org_id.call_count == 0
    assert app_user_repo_mock.is_superuser.call_count == 0
    assert document_repo_mock.get_org_from_import_id.call_count == 0
    assert document_repo_mock.delete.call_count == 0


def test_delete_when_missing(document_repo_mock, app_user_repo_mock):
    document_repo_mock.return_empty = True
    with pytest.raises(ValidationError) as e:
        ok = doc_service.delete("a.b.c.d", USER_EMAIL)
        assert not ok

    expected_msg = "Could not find document a.b.c.d"
    assert e.value.message == expected_msg

    assert document_repo_mock.get.call_count == 1
    assert app_user_repo_mock.get_org_id.call_count == 0
    assert app_user_repo_mock.is_superuser.call_count == 0
    assert document_repo_mock.get_org_from_import_id.call_count == 0
    assert document_repo_mock.delete.call_count == 0


def test_delete_when_no_org_associated_with_entity(
    document_repo_mock, app_user_repo_mock
):
    document_repo_mock.no_org = True
    with pytest.raises(RepositoryError) as e:
        ok = doc_service.delete("a.b.c.d", USER_EMAIL)
        assert not ok

    expected_msg = (
        "The document import id a.b.c.d does not have an associated organisation"
    )
    assert e.value.message == expected_msg

    assert document_repo_mock.get.call_count == 1
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert app_user_repo_mock.is_superuser.call_count == 1
    assert document_repo_mock.get_org_from_import_id.call_count == 1
    assert document_repo_mock.delete.call_count == 0


def test_delete_when_org_mismatch(document_repo_mock, app_user_repo_mock):
    document_repo_mock.alternative_org = True
    with pytest.raises(AuthorisationError) as e:
        ok = doc_service.delete("a.b.c.d", USER_EMAIL)
        assert not ok

    expected_msg = "User 'test@cpr.org' is not authorised to delete document 'a.b.c.d'"
    assert e.value.message == expected_msg

    assert document_repo_mock.get.call_count == 1
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert app_user_repo_mock.is_superuser.call_count == 1
    assert document_repo_mock.get_org_from_import_id.call_count == 1
    assert document_repo_mock.delete.call_count == 0
