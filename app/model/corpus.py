from typing import Optional

from pydantic import AnyHttpUrl, BaseModel

from app.model.general import Json


class CorpusReadDTO(BaseModel):
    """Representation of a Corpus."""

    import_id: str
    title: str
    description: Optional[str] = None
    corpus_text: str
    corpus_image_url: Optional[str] = None
    organisation_id: int
    organisation_name: str

    corpus_type_name: str
    corpus_type_description: str
    metadata: Json
    attribution_url: Optional[str] = None

    # TODO: Add create and last modified timestamps.


class CorpusWriteDTO(BaseModel):
    """Representation of a Corpus."""

    title: str
    description: Optional[str]
    corpus_text: str
    corpus_image_url: Optional[str]

    corpus_type_description: str
    attribution_url: Optional[str] = None


class CorpusCreateDTO(BaseModel):
    """Representation of a Corpus."""

    import_id: Optional[str] = None
    title: str
    description: Optional[str]
    corpus_text: str
    corpus_image_url: Optional[str]
    organisation_id: int
    corpus_type_name: str
    attribution_url: Optional[str] = None


class CorpusLogoUploadDTO(BaseModel):
    """Details required to upload a corpus logo"""

    presigned_upload_url: AnyHttpUrl
    object_cdn_url: AnyHttpUrl
