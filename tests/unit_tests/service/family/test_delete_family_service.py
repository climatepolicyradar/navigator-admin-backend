"""
Tests the family service.

Uses a family repo mock and ensures that the repo is called.
"""

import pytest

import app.service.family as family_service
from app.errors import AuthorisationError, ValidationError


def test_delete(family_repo_mock, organisation_repo_mock, admin_user_context):
    ok = family_service.delete("a.b.c.d", admin_user_context)
    assert ok
    assert family_repo_mock.get.call_count == 1
    assert organisation_repo_mock.get_id_from_name.call_count == 1
    assert family_repo_mock.delete.call_count == 1


def test_delete_when_fam_missing(
    family_repo_mock, organisation_repo_mock, admin_user_context
):
    family_repo_mock.return_empty = True
    ok = family_service.delete("a.b.c.d", admin_user_context)
    assert not ok
    assert family_repo_mock.get.call_count == 1
    assert organisation_repo_mock.get_id_from_name.call_count == 0
    assert family_repo_mock.delete.call_count == 0


def test_delete_raises_when_invalid_id(
    family_repo_mock, organisation_repo_mock, admin_user_context
):
    import_id = "invalid"
    with pytest.raises(ValidationError) as e:
        family_service.delete(import_id, admin_user_context)
    expected_msg = f"The import id {import_id} is invalid!"
    assert e.value.message == expected_msg
    assert family_repo_mock.get.call_count == 0
    assert organisation_repo_mock.get_id_from_name.call_count == 0
    assert family_repo_mock.delete.call_count == 0


def test_delete_raises_when_organisation_invalid(
    family_repo_mock, organisation_repo_mock, app_user_repo_mock, admin_user_context
):
    organisation_repo_mock.error = True
    app_user_repo_mock.error = True
    with pytest.raises(ValidationError) as e:
        ok = family_service.delete("a.b.c.d", admin_user_context)
        assert not ok

    expected_msg = "The organisation name CCLW is invalid!"
    assert e.value.message == expected_msg

    assert family_repo_mock.get.call_count == 1
    assert organisation_repo_mock.get_id_from_name.call_count == 1
    assert app_user_repo_mock.get_org_id.call_count == 0
    assert app_user_repo_mock.is_superuser.call_count == 0
    assert family_repo_mock.delete.call_count == 0


def test_delete_raises_when_family_organisation_mismatch_with_user_org(
    family_repo_mock, organisation_repo_mock, another_admin_user_context
):
    with pytest.raises(AuthorisationError) as e:
        ok = family_service.delete("a.b.c.d", another_admin_user_context)
        assert not ok

    expected_msg = "User 'another-admin@here.com' is not authorised to perform operation on 'a.b.c.d'"
    assert e.value.message == expected_msg

    assert family_repo_mock.get.call_count == 1
    assert organisation_repo_mock.get_id_from_name.call_count == 1
    assert family_repo_mock.delete.call_count == 0


def test_delete_success_when_family_organisation_mismatch_with_user_org(
    family_repo_mock, organisation_repo_mock, super_user_context
):
    ok = family_service.delete("a.b.c.d", super_user_context)
    assert ok

    assert family_repo_mock.get.call_count == 1
    assert organisation_repo_mock.get_id_from_name.call_count == 1
    assert family_repo_mock.delete.call_count == 1
