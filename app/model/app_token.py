from datetime import datetime
from typing import Optional, Union

from pydantic import AnyUrl, BaseModel


class AppTokenCreateDTO(BaseModel):
    """A JSON representation of custom app configurable options.

    allowed_corpora_ids: A list of the corpus import IDs that the custom
        app should show.
    theme: The name of the custom app theme.
    hostname: The hostname of the custom app.
    """

    corpora_ids: list[str]
    theme: str
    hostname: AnyUrl
    expiry_years: Optional[int] = None


class AppTokenReadDTO(BaseModel):
    """A JSON representation of a decoded custom app token."""

    allowed_corpora_ids: list[str]
    sub: str
    aud: str
    iss: str
    exp: Union[float, datetime]
    iat: int
