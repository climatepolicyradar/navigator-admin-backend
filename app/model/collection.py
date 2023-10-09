from pydantic import BaseModel


class CollectionReadDTO(BaseModel):
    """Representation of a Collection for reading."""

    import_id: str
    title: str
    description: str
    families: list[str]
    organisation: str


class CollectionWriteDTO(BaseModel):
    """Representation of a Collection for writing."""

    title: str
    description: str
    organisation: str


class CollectionCreateDTO(BaseModel):
    """Representation of a Collection for creating."""

    title: str
    description: str
    # families: list[str] TODO: Ask Patrick if we want this as an option?
    organisation: str
