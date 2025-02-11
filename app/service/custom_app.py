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
from app.model.custom_app import CustomAppCreateDTO, CustomAppReadDTO
from app.service.corpus import validate

_LOGGER = logging.getLogger(__name__)
TOKEN_SECRET_KEY = os.environ["TOKEN_SECRET_KEY"]
ALGORITHM = "HS256"

CUSTOM_APP_TOKEN_EXPIRE_YEARS: int = 10  # token valid for 10 years
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
    input: CustomAppCreateDTO,
    years: Optional[int] = None,
    db: Optional[Session] = None,
) -> str:
    """Create a custom app configuration token.

    :param CustomAppCreateDTO input: A JSON representation of the
        configurable options for a custom app.
    :param Optional[Session] db: A session to query against.
    :return str: A JWT token containing the encoded allowed corpora.
    """
    if db is None:
        db = db_session.get_db()

    if not all(validate(db, import_id) for import_id in input.corpora_ids):
        raise ValidationError("One or more import IDs don't exist")

    expiry_years = years or CUSTOM_APP_TOKEN_EXPIRE_YEARS
    issued_at = datetime.utcnow()
    expire = issued_at + relativedelta(years=expiry_years)

    config = CustomAppReadDTO(
        allowed_corpora_ids=sorted(input.corpora_ids),
        subject=input.theme,
        issuer=ISSUER,
        audience=input.hostname,
        expiry=expire,
        issued_at=int(
            datetime.timestamp(issued_at.replace(microsecond=0))
        ),  # No microseconds
    )

    if _contains_special_chars(config.subject):
        _LOGGER.error(
            "Subject must not contain any special characters, including spaces"
        )
        raise ValueError

    msg = "Creating custom app configuration token for {input.subject} that "
    msg += f"expires on {expire.strftime('%a %d %B %Y at %H:%M:%S:%f')} "
    msg += f"for the following corpora: {input.corpora_ids}"
    _LOGGER.info(msg)

    to_encode = {
        "allowed_corpora_ids": config.allowed_corpora_ids,
        "exp": config.expiry,
        "iat": config.issued_at,
        "iss": config.issuer,
        "sub": config.subject,
        "aud": str(config.audience),
    }
    return jwt.encode(to_encode, TOKEN_SECRET_KEY, algorithm=ALGORITHM)


def decode(token: str) -> CustomAppReadDTO:
    """Decodes a configuration token.

    :param str token : A JWT token that has been encoded with a list
        of allowed corpora ids that the custom app should show, an
        expiry date and an issued at date.
    :return list[str]: A decoded list of valid corpora ids.
    """
    try:
        decoded_token = jwt.decode(
            token,
            TOKEN_SECRET_KEY,
            algorithms=[ALGORITHM],
            issuer=ISSUER,
        )
    except PyJWTError as e:
        _LOGGER.error(e)
        raise ValidationError("Could not decode configuration token")

    return decoded_token
