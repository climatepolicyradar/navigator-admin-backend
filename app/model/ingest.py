from datetime import datetime
from typing import Optional

from pydantic import AnyHttpUrl, BaseModel

from app.model.collection import CollectionCreateDTO
from app.model.document import DocumentCreateDTO
from app.model.event import EventCreateDTO
from app.model.family import FamilyCreateDTO
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
            import_id=self.import_id,
            title=self.title,
            description=self.description,
        )


class IngestFamilyDTO(BaseModel):
    """Representation of a family for ingest."""

    import_id: str
    title: str
    summary: str
    geographies: list[str]
    category: str
    metadata: Json
    collections: list[str]
    corpus_import_id: str

    def to_family_create_dto(self, corpus_import_id: str) -> FamilyCreateDTO:
        """
        Convert IngestFamilyDTO to FamilyCreateDTO.

        :return FamilyCreateDTO: Converted FamilyCreateDTO instance.
        """
        return FamilyCreateDTO(
            import_id=self.import_id,
            title=self.title,
            summary=self.summary,
            geography=self.geographies,
            category=self.category,
            metadata=self.metadata,
            collections=self.collections,
            corpus_import_id=corpus_import_id,
        )


class IngestEventDTO(BaseModel):
    """Representation of an event for ingest."""

    import_id: str
    family_import_id: str
    family_document_import_id: Optional[str] = None
    event_title: str
    date: datetime
    event_type_value: str

    def to_event_create_dto(self) -> EventCreateDTO:
        """
        Convert IngestEventDTO to EventCreateDTO.

        :return EventCreateDTO: Converted EventCreateDTO instance.
        """
        return EventCreateDTO(
            import_id=self.import_id,
            family_import_id=self.family_import_id,
            event_title=self.event_title,
            date=self.date,
            event_type_value=self.event_type_value,
        )


class IngestDocumentDTO(BaseModel):
    """Representation of a document for ingest."""

    import_id: str
    family_import_id: str
    variant_name: Optional[str] = None
    metadata: Json
    title: str
    source_url: Optional[AnyHttpUrl] = None
    user_language_name: Optional[str] = None

    def to_document_create_dto(self) -> DocumentCreateDTO:
        """
        Convert IngestDocumentDTO to DocumentCreateDTO.

        :return DocumentCreateDTO: Converted DocumentCreateDTO instance.
        """

        return DocumentCreateDTO(
            import_id=self.import_id,
            family_import_id=self.family_import_id,
            variant_name=self.variant_name,
            metadata=self.metadata,
            title=self.title,
            source_url=self.source_url,
            user_language_name=self.user_language_name,
        )
