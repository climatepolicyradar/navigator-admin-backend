from pydantic import BaseModel


class OrganisationReadDTO(BaseModel):
    """Representation of an Organisation."""

    id: int
    internal_name: str
    display_name: str
    description: str
    type: str
