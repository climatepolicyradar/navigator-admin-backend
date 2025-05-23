from datetime import datetime
from typing import Any, Optional, Union

from pydantic import BaseModel


class FamilyReadDTO(BaseModel):
    """A JSON representation of a family."""

    import_id: str
    title: str
    summary: str
    geography: Optional[str] = (
        None  # Todo APP-97: remove default once implemented on the frontend
    )
    geographies: list[str]
    category: str
    status: str
    metadata: dict[str, list[str]]
    slug: str
    events: list[str]
    published_date: Optional[datetime]
    last_updated_date: Optional[datetime]
    documents: list[str]
    collections: list[str]
    organisation: str
    corpus_import_id: str
    corpus_title: str
    corpus_type: str
    created: datetime
    last_modified: datetime
    concepts: Optional[list[dict[str, Any]]] = []


class FamilyWriteDTO(BaseModel):
    """
    A JSON representation of a family for writing.

    Note:
     - import_id is given from the request
     - organisation is immutable
    """

    title: str
    summary: str
    geography: Optional[str] = (
        None  # Todo APP-97: remove default once implemented on the frontend
    )
    geographies: list[str]
    category: str
    metadata: dict[str, list[str]]
    collections: list[str]
    concepts: Optional[list[dict[str, Any]]] = []


class FamilyCreateDTO(BaseModel):
    """
    A JSON representation of a family for creating.

    Note:
     - import_id is auto generated if not supplied
     - slug is auto generated
     - organisation comes from the user's organisation
    """

    import_id: Optional[str] = None
    title: str
    summary: str
    geography: Union[str, list[str]]
    geographies: list[str]
    category: str
    metadata: dict[str, list[str]]
    collections: list[str]
    corpus_import_id: str
    concepts: Optional[list[dict[str, Any]]] = []
