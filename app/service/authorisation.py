import logging

from db_client.models.organisation.authorisation import (
    HTTP_MAP_TO_OPERATION,
    AuthAccess,
    AuthOperation,
)

from app.errors import AuthorisationError
from app.model.authorisation import AUTH_TABLE, AuthEndpoint
from app.model.user import UserContext

_LOGGER = logging.getLogger(__name__)


def http_method_to_operation(method: str) -> AuthOperation:
    """
    Converts from a HTTP method to an AuthOperation

    :param str method: The HTTP method
    :raises AuthorisationError: Raised if it not mappable
    :return AuthOperation: The equivalent AuthOperation
    """
    if method.upper() in HTTP_MAP_TO_OPERATION:
        return HTTP_MAP_TO_OPERATION[method.upper()]
    raise AuthorisationError(f"Unknown HTTP method {method}")


def path_to_endpoint(path: str) -> AuthEndpoint:
    """
    Converts an API path to an AuthEntity

    :param str path: The API path to convert.
    :return AuthEntity: The mapped AuthEntity
    """
    parts = [p.upper() for p in path.split("/")]
    for e in AuthEndpoint:
        if e.value in parts:
            return e
    raise AuthorisationError(f"Cannot get entity from path {path}")


def _has_access(required_access: AuthAccess, user_access: AuthAccess) -> bool:
    if user_access == AuthAccess.SUPER:
        return True
    if required_access == AuthAccess.USER or user_access == required_access:
        return True

    return False


def _get_user_access(user: UserContext) -> AuthAccess:
    if user.is_superuser:
        return AuthAccess.SUPER

    user_auth = user.authorisation
    if (
        user_auth is not None
        and "is_admin" in user_auth.keys()
        and user_auth["is_admin"] is True
    ):
        return AuthAccess.ADMIN

    return AuthAccess.USER


def is_authorised(user: UserContext, entity: AuthEndpoint, op: AuthOperation) -> None:
    required_access = AUTH_TABLE[entity][op]

    if _has_access(required_access, _get_user_access(user)):
        return

    msg = f"User {user.email} is not authorised to {op.name} {_get_article(entity.value)} {entity.name}"
    _LOGGER.error(msg)
    raise AuthorisationError(msg)


def _get_article(word: str) -> str:
    vowels = ["a", "e", "i", "o", "u", "y"]
    if word.lower()[0] in vowels:
        return "an"
    return "a"
