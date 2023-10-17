from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.model.general import Json


class FamilyReadDTO(BaseModel):
    """A JSON representation of a family."""

    import_id: str
    title: str
    summary: str
    geography: str
    category: str
    status: str
    metadata: Json
    slug: str
    events: list[str]
    published_date: Optional[datetime]
    last_updated_date: Optional[datetime]
    documents: list[str]
    collections: list[str]
    organisation: str


class FamilyWriteDTO(BaseModel):
    """A JSON representation of a family for writing."""

    # import_id: not included as this is in the request path
    title: str
    summary: str
    geography: str
    category: str
    metadata: Json
    # organisation: not included as once created is immutable


class FamilyCreateDTO(BaseModel):
    """A JSON representation of a family for creating."""

    # import_id: not included as generated
    title: str
    summary: str
    geography: str
    category: str
    metadata: Json
    # slug: not included as this is generated from title
    organisation: str  # FIXME: should this be the org of the current user?
