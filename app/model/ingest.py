from datetime import datetime
from typing import Optional

from pydantic import AnyHttpUrl, BaseModel

from app.model.collection import CollectionCreateDTO
from app.model.general import Json


class IngestCollectionDTO(BaseModel):
    """Representation of a collection for ingest."""

    import_id: str
    title: str
    description: str

    def to_collection_create_dto(self) -> CollectionCreateDTO:
        """
        Convert IngestCollectionDTO to CollectionCreateDTO.

        :return CollectionCreateDTO: Converted CollectionCreateDTO instance.
        """
        return CollectionCreateDTO(
            import_id=self.import_id, title=self.title, description=self.description
        )


class IngestFamilyDTO(BaseModel):
    """
    A JSON representation of a family for ingest.

    Note:
     - corpus_import_id is auto populated
     - slug is auto generated
     - organisation comes from the user's organisation
    """

    import_id: str
    title: str
    summary: str
    geography: str
    category: str
    metadata: Json
    collections: list[str]
    corpus_import_id: str


class IngestEventDTO(BaseModel):
    """
    JSON Representation of an event for ingest.

    """

    import_id: str
    event_title: str
    date: datetime
    event_type_value: str

    family_import_id: str
    family_document_import_id: Optional[str] = None


class IngestDocumentDTO(BaseModel):
    """Representation of a document for ingest."""

    family_import_id: str
    variant_name: Optional[str] = None
    metadata: Json
    events: IngestEventDTO
    title: str
    source_url: Optional[AnyHttpUrl] = None
    user_language_name: Optional[str]
