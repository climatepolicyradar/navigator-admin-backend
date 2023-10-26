import logging
import jwt
import os
from datetime import datetime, timedelta
from typing import Any, Optional
from app.errors import TokenError

from app.model.jwt_user import JWTUser


SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 8 * 60  # 8 hours for access token


_LOGGER = logging.getLogger(__name__)


def encode(
    email: str, is_superuser: bool, authorisation: dict, minutes: Optional[int] = None
) -> str:
    """
    Encodes the user's data into a JWT token.

    :param str email: User's email
    :param bool is_superuser: User's ability to be a superuser.
    :param dict authorisation: Authorisation information (not yet fully spec'd)
    :param Optional[int] minutes: TTL for the token
    :return str: The encoded token
    """

    if "@" not in email or "." not in email:
        raise TokenError(f"Parameter email should be an email, not {email}")

    if type(authorisation) != dict:
        raise TokenError(
            f"Parameter authorisation should be a dict, not {authorisation}"
        )

    if type(is_superuser) != bool:
        raise TokenError(f"Parameter is_superuser should be a bool, not {is_superuser}")

    to_encode = {
        "sub": email,
        "email": email,
        "is_superuser": is_superuser,
        "authorisation": authorisation,
    }
    expiry_minutes = minutes or ACCESS_TOKEN_EXPIRE_MINUTES
    expire = datetime.utcnow() + timedelta(minutes=expiry_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode(token: str) -> JWTUser:
    """
    Decodes the JWT token into a JWTUser.

    :param str token: The token to decode.
    :raises TokenError: If cannot decode the string
    :raises TokenError: If the decoded token does not contain the necessary
    information to create a JWTUser.
    :return JWTUser: The decoded user.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        _LOGGER.exception(f"Error when decoding: {token}")
        raise TokenError("Payload cannot be decoded")

    email: Optional[str] = payload.get("email")
    if email is None:
        raise TokenError("Token did not contain an email")

    authorisation: Optional[dict[str, Any]] = payload.get("authorisation", {})

    jwt_user = JWTUser(
        email=email,
        is_superuser=payload.get("is_superuser", False),
        authorisation=authorisation,
    )
    return jwt_user
