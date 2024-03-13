from typing import Optional

from pydantic import BaseModel


class SummaryDTO(BaseModel):
    """Representation of an Analytics Summary."""

    n_documents: Optional[int]
    n_families: Optional[int]
    n_collections: Optional[int]
    n_events: Optional[int]
