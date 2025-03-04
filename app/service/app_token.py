import logging
import os
from datetime import datetime
from typing import Optional

import jwt
from dateutil.relativedelta import relativedelta
from jwt import PyJWTError
from sqlalchemy.orm import Session

import app.clients.db.session as db_session
from app.errors import ValidationError
from app.model.app_token import AppTokenCreateDTO, AppTokenReadDTO
from app.service.corpus import validate_list

_LOGGER = logging.getLogger(__name__)
ALGORITHM = "HS256"

APP_TOKEN_EXPIRE_YEARS: int = 10  # token valid for 10 years
ISSUER: str = "Climate Policy Radar"


def _contains_special_chars(input: str) -> bool:
    """Check if string contains any non alpha numeric characters.

    :param str input: A string to check.
    :return bool: True if string contains special chars, False otherwise.
    """
    if any(not char.isalnum() for char in input):
        return True
    return False


def create_configuration_token(
    input: AppTokenCreateDTO,
    years: Optional[int] = None,
    db: Optional[Session] = None,
) -> str:
    """Create a custom app configuration token.

    :param AppTokenCreateDTO input: A JSON representation of the
        configurable options for a custom app.
    :param Optional[int] years: Number of years until token expiry,
        defaults to None
    :param Optional[Session] db: A database session to query against,
        defaults to None
    :return str: A JWT token containing the encoded allowed corpora
    :raises ValidationError: If theme contains special chars, corpora
        don't exist, or config is invalid.
    """
    token_secret = os.environ.get("TOKEN_SECRET_KEY")
    if token_secret is None:
        _LOGGER.error("TOKEN_SECRET_KEY environment variable not set")
        raise ValidationError("TOKEN_SECRET_KEY is not set")

    if db is None:
        db = db_session.get_db()

    if _contains_special_chars(input.theme):
        _LOGGER.error("Theme must not contain special characters, including spaces")
        raise ValidationError("Invalid subject provided")

    if not validate_list(db, input.corpora_ids):
        _LOGGER.error("One or more corpus IDs do not exist")
        raise ValidationError("One or more import IDs don't exist")

    expiry_years = years or APP_TOKEN_EXPIRE_YEARS
    issued_at = datetime.utcnow()
    expire = issued_at + relativedelta(years=expiry_years)

    config = AppTokenReadDTO(
        allowed_corpora_ids=sorted(input.corpora_ids),
        sub=input.theme,
        iss=ISSUER,
        aud=str(input.hostname.host if input.hostname.host is not None else ""),
        exp=int(datetime.timestamp(expire.replace(microsecond=0))),
        iat=int(datetime.timestamp(issued_at.replace(microsecond=0))),
    )

    if config.aud in [None, ""]:
        _LOGGER.error("Host must not be empty or None")
        raise ValidationError("Invalid audience provided")

    _LOGGER.info(
        f"Creating token for {input.theme} expiring {expire.strftime('%Y-%m-%d %H:%M:%S')} "
        f"with corpora: {input.corpora_ids}"
    )
    print(
        f"Creating token for {input.theme} expiring {expire.strftime('%Y-%m-%d %H:%M:%S')} "
        f"with corpora: {input.corpora_ids}"
    )
    print(config.model_dump(mode="json"))
    return jwt.encode(config.model_dump(mode="json"), token_secret, algorithm=ALGORITHM)


def decode(token: str) -> AppTokenReadDTO:
    """Decodes a configuration token.

    :param str token : A JWT token that has been encoded with a list
        of allowed corpora ids that the custom app should show, an
        expiry date and an issued at date.
    :return list[str]: A decoded list of valid corpora ids.
    """
    token_secret = os.environ.get("TOKEN_SECRET_KEY")
    if token_secret is None:
        raise ValidationError("TOKEN_SECRET_KEY is not set")

    try:
        decoded_token = jwt.decode(
            token,
            token_secret,
            algorithms=[ALGORITHM],
            issuer=ISSUER,
            options={"verify_aud": False},
        )
    except PyJWTError as e:
        _LOGGER.error(e)
        raise ValidationError("Could not decode configuration token")

    print(decoded_token)
    return decoded_token
