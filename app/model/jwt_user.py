from typing import Any, Mapping, Optional

from pydantic import BaseModel


class JWTUser(BaseModel):
    """An object representing what is in the token."""

    email: str
    is_superuser: bool = False
    authorisation: Optional[Mapping[str, Any]] = None
