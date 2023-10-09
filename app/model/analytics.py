from pydantic import BaseModel
from typing import Optional


class SummaryDTO(BaseModel):
    """Representation of an Analytics Summary."""

    n_documents: Optional[int]
    n_families: Optional[int]
    n_collections: Optional[int]
    n_events: Optional[int]
