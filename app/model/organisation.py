from pydantic import BaseModel


class OrganisationReadDTO(BaseModel):
    """Representation of an Organisation."""

    id: int
    internal_name: str
    display_name: str
    description: str
    type: str
    attribution_url: str


class OrganisationCreateDTO(BaseModel):
    """Representation of an Organisation for creating."""

    internal_name: str
    display_name: str
    description: str
    type: str
    attribution_url: str


class OrganisationWriteDTO(BaseModel):
    """Representation of an Organisation for updating."""

    internal_name: str
    display_name: str
    description: str
    type: str
    attribution_url: str
