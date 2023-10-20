from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.clients.db.models.law_policy.family import EventStatus


class EventReadDTO(BaseModel):
    """
    JSON Representation of the DTO for reading an event.

    TODO: Add family document fields here including family title,
    family document title, maybe geography etc.?
    """

    # From FamilyEvent
    import_id: str
    event_title: str
    date: datetime
    event_type_value: str
    event_status: EventStatus

    # From FamilyDocument
    family_import_id: str
    family_document_import_id: Optional[str] = None


class EventCreateDTO(BaseModel):
    """
    JSON Representation of the DTO for creating an event.

    We don't need to specify the import_id because this will be auto-
    generated.
    """

    # From FamilyEvent
    event_title: str
    date: datetime
    event_type_value: str
    event_status: EventStatus

    # From FamilyDocument
    family_import_id: str
    family_document_import_id: Optional[str] = None


class EventWriteDTO(BaseModel):
    """
    JSON Representation of the DTO for writing an event.

    The following fields are immutable:
    - family_import_id
    - import_id
    - family_document_import_id
    - event_status
    """

    event_title: str
    date: datetime
    event_type_value: str
