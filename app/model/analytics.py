from pydantic import BaseModel


class SummaryDTO(BaseModel):
    """Representation of an Analytics Summary."""

    n_documents: int
    n_families: int
    n_collections: int
    n_events: int
