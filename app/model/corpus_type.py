from pydantic import BaseModel

from app.model.general import Json


class CorpusTypeReadDTO(BaseModel):
    """Representation of a Corpus Type."""

    name: str
    description: str
    metadata: Json


class CorpusTypeCreateDTO(BaseModel):
    """Representation of a Corpus Type."""

    name: str
    description: str
    metadata: Json
