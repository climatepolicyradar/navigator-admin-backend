from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.model.general import Json


class IngestCollectionDTO(BaseModel):
    """Representation of a collection for ingest."""

    import_id: str
    title: str
    description: str


class IngestFamilyDTO(BaseModel):
    """
    A JSON representation of a family for ingest.

    Note:
     - corpus_import_id is auto populated
     - slug is auto generated
     - organisation comes from the user's organisation
    """

    import_id: str
    title: str
    summary: str
    geography: str
    category: str
    metadata: Json
    collections: list[str]
    corpus_import_id: str


class IngestEventDTO(BaseModel):
    """
    JSON Representation of an event for ingest.

    """

    import_id: str
    event_title: str
    date: datetime
    event_type_value: str

    family_import_id: str
    family_document_import_id: Optional[str] = None
