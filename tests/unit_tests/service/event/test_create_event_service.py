from unittest.mock import patch

import pytest

import app.service.event as event_service
from app.errors import AuthorisationError, RepositoryError, ValidationError
from tests.helpers.event import create_event_create_dto


@patch("app.service.metadata.db_client_metadata.validate_metadata", return_value=None)
def test_create(
    mock_validate_metadata,
    event_repo_mock,
    family_repo_mock,
    admin_user_context,
):
    new_event = create_event_create_dto()
    event = event_service.create(new_event, admin_user_context)
    assert event is not None
    assert event_repo_mock.create.call_count == 1
    assert family_repo_mock.get_organisation.call_count == 1
    assert family_repo_mock.get.call_count == 1
    assert mock_validate_metadata.call_count == 1


@patch("app.service.metadata.db_client_metadata.validate_metadata", return_value=None)
def test_create_when_db_fails(
    mock_validate_metadata,
    event_repo_mock,
    family_repo_mock,
    admin_user_context,
):
    new_event = create_event_create_dto()
    event_repo_mock.throw_repository_error = True

    with pytest.raises(RepositoryError):
        event_service.create(new_event, admin_user_context)
    assert event_repo_mock.create.call_count == 1
    assert family_repo_mock.get_organisation.call_count == 1
    assert family_repo_mock.get.call_count == 1
    assert mock_validate_metadata.call_count == 1


def test_create_raises_when_invalid_family_id(
    family_repo_mock, event_repo_mock, admin_user_context
):
    new_event = create_event_create_dto(family_import_id="invalid family")
    with pytest.raises(ValidationError) as e:
        event_service.create(new_event, admin_user_context)
    expected_msg = f"The import id {new_event.family_import_id} is invalid!"
    assert e.value.message == expected_msg
    assert family_repo_mock.get.call_count == 0
    assert family_repo_mock.get_organisation.call_count == 0
    assert event_repo_mock.create.call_count == 0


def test_create_when_no_org_associated_with_entity(
    event_repo_mock, family_repo_mock, admin_user_context
):
    family_repo_mock.no_org = True
    new_event = create_event_create_dto()
    with pytest.raises(ValidationError) as e:
        event_service.create(new_event, admin_user_context)

    expected_msg = "No organisation associated with import id test.family.1.0"
    assert e.value.message == expected_msg

    assert family_repo_mock.get.call_count == 1
    assert family_repo_mock.get_organisation.call_count == 1
    assert event_repo_mock.create.call_count == 0


def test_create_raises_when_org_mismatch(
    event_repo_mock, family_repo_mock, another_admin_user_context
):
    family_repo_mock.alternative_org = True
    new_event = create_event_create_dto()
    with pytest.raises(AuthorisationError) as e:
        event_service.create(new_event, another_admin_user_context)

    expected_msg = "User 'another-admin@here.com' is not authorised to perform operation on 'test.family.1.0'"
    assert e.value.message == expected_msg

    assert family_repo_mock.get.call_count == 1
    assert family_repo_mock.get_organisation.call_count == 1
    assert event_repo_mock.create.call_count == 0


@patch("app.service.metadata.db_client_metadata.validate_metadata", return_value=None)
def test_create_success_when_org_mismatch(
    mock_validate_metadata,
    event_repo_mock,
    family_repo_mock,
    super_user_context,
):
    new_event = create_event_create_dto()
    event = event_service.create(new_event, super_user_context)
    assert event is not None
    assert event_repo_mock.create.call_count == 1
    assert family_repo_mock.get_organisation.call_count == 1
    assert family_repo_mock.get.call_count == 1
    assert mock_validate_metadata.call_count == 1


@patch(
    "app.service.metadata.db_client_metadata.validate_metadata",
    return_value=["error1", "error2"],
)
def test_create_raises_when_invalid_metadata(
    mock_validate_metadata,
    event_repo_mock,
    family_repo_mock,
    admin_user_context,
):
    new_event = create_event_create_dto()

    with pytest.raises(ValidationError) as e:
        event_service.create(new_event, admin_user_context)

    expected_msg = "Metadata validation failed: error1,error2"
    assert e.value.message == expected_msg

    assert family_repo_mock.get_organisation.call_count == 1
    assert family_repo_mock.get.call_count == 1
    assert mock_validate_metadata.call_count == 1
    assert event_repo_mock.create.call_count == 0


@patch(
    "app.service.metadata.db_client_metadata.validate_metadata", side_effect=TypeError
)
def test_create_raises_type_error(
    mock_validate_metadata,
    event_repo_mock,
    family_repo_mock,
    admin_user_context,
):
    new_event = create_event_create_dto()

    with pytest.raises(ValidationError):
        event_service.create(new_event, admin_user_context)

    assert family_repo_mock.get_organisation.call_count == 1
    assert family_repo_mock.get.call_count == 1
    assert mock_validate_metadata.call_count == 1
    assert event_repo_mock.create.call_count == 0
