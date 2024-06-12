from typing import Any, Mapping, Optional

from pydantic import BaseModel


class UserContext(BaseModel):
    """An object representing what is in the token."""

    email: str
    org_id: int
    is_superuser: bool = False
    authorisation: Optional[Mapping[str, Any]] = None
