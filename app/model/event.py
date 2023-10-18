from datetime import datetime
from pydantic import BaseModel
from typing import Optional

from app.clients.db.models.law_policy.family import (
    EventStatus,
)


class EventReadDTO(BaseModel):
    """JSON Representation of a Event for reading."""

    # From FamilyEvent
    import_id: str
    event_title: str
    date: datetime
    event_type_value: str
    family_import_id: str
    family_document_import_id: Optional[str] = None
    event_status: EventStatus
