from typing import Optional

from pydantic import BaseModel

from app.model.general import Json


class CorpusReadDTO(BaseModel):
    """Representation of a Corpus."""

    import_id: str
    title: str
    description: str
    corpus_text: Optional[str]
    corpus_image_url: Optional[str] = None
    organisation_id: int
    organisation_name: str

    corpus_type_name: str
    corpus_type_description: str
    metadata: Json

    # TODO: Add create and last modified timestamps.


class CorpusWriteDTO(BaseModel):
    """Representation of a Corpus."""

    title: str
    description: str
    corpus_text: Optional[str]
    corpus_image_url: Optional[str]

    corpus_type_description: str


class CorpusCreateDTO(BaseModel):
    """Representation of a Corpus."""

    import_id: Optional[str] = None
    title: str
    description: str
    corpus_text: Optional[str]
    corpus_image_url: Optional[str]
    organisation_id: int
    corpus_type_name: str
