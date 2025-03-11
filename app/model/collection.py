from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CollectionReadDTO(BaseModel):
    """Representation of a Collection for reading."""

    import_id: str
    title: str
    description: str
    families: list[str]
    organisation: str
    created: datetime
    last_modified: datetime
    valid_metadata: dict[str, list[str]]


class CollectionWriteDTO(BaseModel):
    """Representation of a Collection for writing."""

    title: str
    description: str
    organisation: str
    valid_metadata: dict[str, list[str]]


class CollectionCreateDTO(BaseModel):
    """Representation of a Collection for creating."""

    import_id: Optional[str] = None
    title: str
    description: str
    valid_metadata: dict[str, list[str]]
