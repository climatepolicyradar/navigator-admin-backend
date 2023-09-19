from pydantic import BaseModel


class CollectionReadDTO(BaseModel):
    """Representation of a Collection."""

    import_id: str
    title: str
    description: str
    families: list[str]
    organisation: str


class CollectionWriteDTO(BaseModel):
    """Representation of a Collection for writing."""

    import_id: str
    title: str
    description: str
    organisation: str
