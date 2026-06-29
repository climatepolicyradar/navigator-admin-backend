from typing import Any, Mapping, Optional

from pydantic import BaseModel


class UserContext(BaseModel):
    """An object representing what is in the token."""

    email: str
    org_id: Optional[int] = None
    org_ids: list[int] = []
    is_superuser: bool = False
    authorisation: Optional[Mapping[str, Any]] = None


class OrgMembership(BaseModel):
    """A single organisation membership entry."""

    id: int
    is_admin: bool = False


class UserReadDTO(BaseModel):
    """Representation of a user returned from the API."""

    email: str
    name: str | None
    is_superuser: bool
    organisations: list[OrgMembership]


class UserWriteDTO(BaseModel):
    """Payload for updating a user's name and organisation memberships."""

    name: str | None = None
    organisations: list[OrgMembership]
