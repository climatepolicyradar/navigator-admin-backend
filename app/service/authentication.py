import logging
from typing import cast

from passlib.context import CryptContext
from sqlalchemy.exc import NoResultFound

import app.clients.db.session as db_session
import app.service.token as token_service
from app.errors import AuthenticationError, RepositoryError
from app.repository import app_user_repo

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_LOGGER = logging.getLogger(__name__)


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

    org_id = None
    with db_session.get_db_session() as db:
        try:
            user = app_user_repo.get_user_by_email(db, email)
        except NoResultFound:
            user = None

        if user is None:
            _LOGGER.error(f"Failed login attempt, user not found for {email}")
            raise RepositoryError(f"User not found for {email}")
        if not app_user_repo.is_active(db, email):
            _LOGGER.error(f"Failed login attempt as inactive for {email}")
            raise AuthenticationError(f"User {email} is marked as not active.")

        org_id = app_user_repo.get_org_id(db, cast(str, user.email))
        if org_id is None:
            _LOGGER.error(f"Failed login attempt, org not found for {email}")
            raise RepositoryError(f"Organisation not found for {email}")

        hash = str(user.hashed_password)
        if len(hash) == 0 or not verify_password(password, hash):
            _LOGGER.error(f"Failed login attempt for password mismatch for {email}")
            raise AuthenticationError(f"Could not verify password for {email}")

        app_user_links = app_user_repo.get_app_user_authorisation(db, user)

    authorisation = {
        cast(str, org.name): {"is_admin": cast(bool, org_user.is_admin)}
        for org_user, org in app_user_links
        if org.id == org_id
    }

    return token_service.encode(
        email, org_id, cast(bool, user.is_superuser), authorisation
    )
