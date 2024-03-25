import pytest

import app.service.authentication as auth_service
import app.service.token as token_service
from app.errors import AuthenticationError, RepositoryError
from tests.unit_tests.mocks.repos.app_user_repo import (
    HASH_PASSWORD,
    PLAIN_PASSWORD,
    VALID_USERNAME,
)


def test_password_hash_matches():
    assert auth_service.verify_password(PLAIN_PASSWORD, HASH_PASSWORD) is True


def test_raises_when_user_not_found(
    app_user_repo_mock,
):
    app_user_repo_mock.error = True
    with pytest.raises(RepositoryError) as e:
        auth_service.authenticate_user(VALID_USERNAME, PLAIN_PASSWORD)

    assert e.value.message == f"User not found for {VALID_USERNAME}"
    assert app_user_repo_mock.get_user_by_email.call_count == 1


def test_raises_when_incorrect_password(
    app_user_repo_mock,
):
    with pytest.raises(AuthenticationError) as e:
        auth_service.authenticate_user(VALID_USERNAME, "random")

    assert e.value.message == f"Could not verify password for {VALID_USERNAME}"
    assert app_user_repo_mock.get_user_by_email.call_count == 1


def test_raises_when_no_password(
    app_user_repo_mock,
):
    with pytest.raises(AuthenticationError) as e:
        auth_service.authenticate_user(VALID_USERNAME, "")

    assert e.value.message == f"Could not verify password for {VALID_USERNAME}"
    assert app_user_repo_mock.get_user_by_email.call_count == 1


def test_raises_when_inactive(
    app_user_repo_mock,
):
    app_user_repo_mock.user_active = False
    with pytest.raises(AuthenticationError) as e:
        auth_service.authenticate_user(VALID_USERNAME, PLAIN_PASSWORD)

    assert e.value.message == f"User {VALID_USERNAME} is marked as not active."
    assert app_user_repo_mock.get_user_by_email.call_count == 1


def test_can_auth(
    app_user_repo_mock,
):
    token = auth_service.authenticate_user(VALID_USERNAME, PLAIN_PASSWORD)
    user = token_service.decode(token)

    assert user.email == VALID_USERNAME
    assert user.is_superuser is True
    assert user.authorisation is not None
    assert len(user.authorisation.keys()) == 0

    assert app_user_repo_mock.get_user_by_email.call_count == 1
    assert app_user_repo_mock.get_app_user_authorisation.call_count == 1
