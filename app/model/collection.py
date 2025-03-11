from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.model.general import Json


class CollectionReadDTO(BaseModel):
    """Representation of a Collection for reading."""

    import_id: str
    title: str
    description: str
    metadata: Json
    families: list[str]
    organisation: str
    created: datetime
    last_modified: datetime


class CollectionWriteDTO(BaseModel):
    """Representation of a Collection for writing."""

    title: str
    description: str
    organisation: str


class CollectionCreateDTO(BaseModel):
    """Representation of a Collection for creating."""

    import_id: Optional[str] = None
    title: str
    description: str
    metadata: Json
