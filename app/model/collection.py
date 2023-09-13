from pydantic import BaseModel


class CollectionDTO(BaseModel):
    """Representation of a Collection."""

    import_id: str
    title: str
    description: str
    families: list[str]
    organisation: str
