from typing import cast

from passlib.context import CryptContext

import app.db.session as db_session
from app.errors import AuthenticationError, RepositoryError
import app.repository.app_user as app_user_repo
import app.service.token as token_service

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """
    Gets the hash of a password.

    :param str password: The plain text password.
    :return str: The hash of the password.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies the password matches the against the stored hash.

    :param str plain_password: The plain text password.
    :param str hashed_password: The stored hash.
    :return bool: True if matches
    """
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(email: str, password: str) -> str:
    """
    Authenticates a user and returns a JWT token.

    :param str email: The user's email.
    :param str password: The user's password.
    :raises RepositoryError: Raised when the user is not found.
    :raises AuthenticationError: Raised when password does not match.
    :return str: The JWT token.
    """

    with db_session.get_db() as db:
        user = app_user_repo.get_user_by_email(db, email)

        if user is None:
            raise RepositoryError(f"User not found for {email}")

        if not verify_password(password, str(user.hashed_password)):
            # TODO: Log failed login attempt?
            raise AuthenticationError(f"Could not verify password for {email}")

        app_user_links = app_user_repo.get_app_user_authorisation(db, user)

    authorisation = {
        cast(str, org.name): {"is_admin": cast(bool, org_user.is_admin)}
        for org_user, org in app_user_links
    }

    return token_service.encode(email, cast(bool, user.is_superuser), authorisation)
