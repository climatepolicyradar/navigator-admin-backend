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
    """
    A JSON representation of a family for writing.

    Note:
     - import_id is given from the request
     - organisation is immutable
    """

    title: str
    summary: str
    geography: str
    category: str
    metadata: Json
    collections: list[str]


class FamilyCreateDTO(BaseModel):
    """
    A JSON representation of a family for creating.

    Note:
     - import_id is auto generated
     - slug is auto generated
     - organisation comes from the user's organisation
    """

    title: str
    summary: str
    geography: str
    category: str
    metadata: Json
    collections: list[str]
