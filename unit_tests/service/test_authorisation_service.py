import pytest
from app.errors.authentication_error import AuthenticationError
from app.errors.repository_error import RepositoryError
import app.service.authentication as auth_service
import app.service.token as token_service
from unit_tests.mocks.app_user_repo import HASH_PASSWORD, PLAIN_PASSWORD


def test_password_hash_matches():
    assert auth_service.verify_password(PLAIN_PASSWORD, HASH_PASSWORD) is True


def test_auth_user_raises_when_no_user(
    app_user_repo_mock,
):
    app_user_repo_mock.error = True
    with pytest.raises(RepositoryError) as e:
        auth_service.authenticate_user("bob@here.com", PLAIN_PASSWORD)

    assert e.value.message == "User not found for bob@here.com"
    assert app_user_repo_mock.get_user_by_email.call_count == 1


def test_auth_user_raises_when_no_match(
    app_user_repo_mock,
):
    with pytest.raises(AuthenticationError) as e:
        auth_service.authenticate_user("bob@here.com", "random")

    assert e.value.message == "Could not verify password for bob@here.com"
    assert app_user_repo_mock.get_user_by_email.call_count == 1


def test_auth_user_raises_when_no_password(
    app_user_repo_mock,
):
    with pytest.raises(AuthenticationError) as e:
        auth_service.authenticate_user("bob@here.com", "")

    assert e.value.message == "Could not verify password for bob@here.com"
    assert app_user_repo_mock.get_user_by_email.call_count == 1


def test_auth_user_can_auth(
    app_user_repo_mock,
):
    token = auth_service.authenticate_user("bob@here.com", PLAIN_PASSWORD)
    user = token_service.decode(token)

    assert user.email == "bob@here.com"
    assert user.is_superuser is True
    assert user.authorisation is not None
    assert len(user.authorisation.keys()) == 0
