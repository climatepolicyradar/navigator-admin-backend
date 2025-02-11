from datetime import datetime
from typing import Optional, Union

from pydantic import AnyUrl, BaseModel


class CustomAppCreateDTO(BaseModel):
    """A JSON representation of custom app configurable options.

    allowed_corpora_ids: A list of the corpus import IDs that the custom
        app should show.
    theme: The name of the custom app theme.
    hostname: The hostname of the custom app.
    """

    corpora_ids: list[str]
    theme: str
    hostname: AnyUrl
    expiry_years: Optional[int]


class CustomAppReadDTO(BaseModel):
    """A JSON representation of a decoded custom app token."""

    allowed_corpora_ids: list[str]
    subject: str
    audience: str
    issuer: str
    expiry: Union[float, datetime]
    issued_at: int
