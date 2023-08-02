from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class FamilyDTO(BaseModel):
    """A JSON representation of a family."""

    # TODO organisation: str
    import_id: str
    title: str
    summary: str
    geography: str
    category: str
    status: str
    metadata: dict
    slug: str
    events: list[str]
    published_date: Optional[datetime]
    last_updated_date: Optional[datetime]
    documents: list[str]
    collections: list[str]
    organisation: str
