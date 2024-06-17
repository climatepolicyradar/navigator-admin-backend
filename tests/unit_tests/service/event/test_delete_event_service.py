import pytest

import app.service.event as event_service
from app.errors import AuthorisationError, ValidationError


def test_delete(event_repo_mock, admin_user_context):
    ok = event_service.delete("a.b.c.d", admin_user_context)
    assert ok
    assert event_repo_mock.get.call_count == 1
    assert event_repo_mock.get_org_from_import_id.call_count == 1
    assert event_repo_mock.delete.call_count == 1


def test_delete_returns_false_when_missing(event_repo_mock, admin_user_context):
    event_repo_mock.return_empty = True
    ok = event_service.delete("a.b.c.d", admin_user_context)
    assert not ok
    assert event_repo_mock.get.call_count == 1
    assert event_repo_mock.get_org_from_import_id.call_count == 0
    assert event_repo_mock.delete.call_count == 0


def test_delete_raises_when_invalid_id(event_repo_mock, admin_user_context):
    import_id = "invalid"
    with pytest.raises(ValidationError) as e:
        event_service.delete(import_id, admin_user_context)
    expected_msg = f"The import id {import_id} is invalid!"
    assert e.value.message == expected_msg
    assert event_repo_mock.get.call_count == 0
    assert event_repo_mock.get_org_from_import_id.call_count == 0
    assert event_repo_mock.delete.call_count == 0


def test_delete_when_no_org_associated_with_entity(event_repo_mock, admin_user_context):
    event_repo_mock.no_org = True
    with pytest.raises(ValidationError) as e:
        ok = event_service.delete("a.b.c.d", admin_user_context)
        assert not ok

    expected_msg = "No organisation associated with import id a.b.c.d"
    assert e.value.message == expected_msg

    assert event_repo_mock.get.call_count == 1
    assert event_repo_mock.get_org_from_import_id.call_count == 1
    assert event_repo_mock.delete.call_count == 0


def test_delete_raises_when_org_mismatch(event_repo_mock, admin_user_context):
    event_repo_mock.alternative_org = True
    with pytest.raises(AuthorisationError) as e:
        ok = event_service.delete("a.b.c.d", admin_user_context)
        assert not ok

    expected_msg = (
        "User 'admin@here.com' is not authorised to perform operation on 'a.b.c.d'"
    )
    assert e.value.message == expected_msg

    assert event_repo_mock.get.call_count == 1
    assert event_repo_mock.get_org_from_import_id.call_count == 1
    assert event_repo_mock.delete.call_count == 0


def test_delete_success_when_org_mismatch_super(event_repo_mock, super_user_context):

    ok = event_service.delete("a.b.c.d", super_user_context)
    assert ok
    assert event_repo_mock.get.call_count == 1
    assert event_repo_mock.get_org_from_import_id.call_count == 1
    assert event_repo_mock.delete.call_count == 1
