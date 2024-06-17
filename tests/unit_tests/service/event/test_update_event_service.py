import pytest

import app.service.event as event_service
from app.errors import AuthorisationError, RepositoryError, ValidationError
from tests.helpers.event import create_event_write_dto


def test_update(event_repo_mock, admin_user_context):
    result = event_service.update(
        "a.b.c.d", create_event_write_dto(), admin_user_context
    )
    assert result is not None
    assert event_repo_mock.get.call_count == 2
    assert event_repo_mock.get_org_from_import_id.call_count == 1
    assert event_repo_mock.update.call_count == 1


def test_update_when_db_error(event_repo_mock, admin_user_context):
    event_repo_mock.throw_repository_error = True

    with pytest.raises(RepositoryError) as e:
        event_service.update("a.b.c.d", create_event_write_dto(), admin_user_context)
    assert e.value.message == "bad event repo"
    assert event_repo_mock.get.call_count == 1
    assert event_repo_mock.get_org_from_import_id.call_count == 1
    assert event_repo_mock.update.call_count == 1


def test_update_when_event_missing(event_repo_mock, admin_user_context):
    event_repo_mock.return_empty = True

    ok = event_service.update("a.b.c.d", create_event_write_dto(), admin_user_context)
    assert not ok
    assert event_repo_mock.get.call_count == 1
    assert event_repo_mock.get_org_from_import_id.call_count == 0
    assert event_repo_mock.update.call_count == 0


def test_update_raises_when_invalid_id(event_repo_mock, admin_user_context):
    with pytest.raises(ValidationError) as e:
        event_service.update("invalid", create_event_write_dto(), admin_user_context)
    expected_msg = "The import id invalid is invalid!"
    assert e.value.message == expected_msg
    assert event_repo_mock.get.call_count == 0
    assert event_repo_mock.get_org_from_import_id.call_count == 0
    assert event_repo_mock.update.call_count == 0


def test_update_when_no_org_associated_with_entity(event_repo_mock, admin_user_context):
    event_repo_mock.no_org = True
    with pytest.raises(ValidationError) as e:
        ok = event_service.update(
            "a.b.c.d", create_event_write_dto(), admin_user_context
        )
        assert not ok

    expected_msg = "No organisation associated with import id a.b.c.d"
    assert e.value.message == expected_msg

    assert event_repo_mock.get_org_from_import_id.call_count == 1
    assert event_repo_mock.update.call_count == 0
    assert event_repo_mock.get.call_count == 1


def test_update_raises_when_org_mismatch(event_repo_mock, another_admin_user_context):
    event_repo_mock.alternative_org = True
    with pytest.raises(AuthorisationError) as e:
        event_service.update(
            "a.b.c.d",
            create_event_write_dto(),
            another_admin_user_context,
        )

    expected_msg = "User 'another-admin@here.com' is not authorised to perform operation on 'a.b.c.d'"
    assert e.value.message == expected_msg

    assert event_repo_mock.get_org_from_import_id.call_count == 1
    assert event_repo_mock.update.call_count == 0
    assert event_repo_mock.get.call_count == 1


def test_update_success_when_org_mismatch_superuser(
    event_repo_mock, super_user_context
):
    result = event_service.update(
        "a.b.c.d", create_event_write_dto(), super_user_context
    )
    assert result is not None
    assert event_repo_mock.get.call_count == 2
    assert event_repo_mock.get_org_from_import_id.call_count == 1
    assert event_repo_mock.update.call_count == 1
