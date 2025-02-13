from datetime import datetime
from typing import Dict, List, Optional, Union

from pydantic import AnyHttpUrl, BaseModel, RootModel

from app.model.collection import CollectionCreateDTO, CollectionWriteDTO
from app.model.document import DocumentCreateDTO
from app.model.event import EventCreateDTO
from app.model.family import FamilyCreateDTO, FamilyWriteDTO

Metadata = RootModel[Dict[str, Union[str, List[str]]]]


class BulkImportCollectionDTO(BaseModel):
    """Representation of a collection for bulk import."""

    import_id: str
    title: str
    description: str

    def to_collection_create_dto(self) -> CollectionCreateDTO:
        """
        Convert BulkImportCollectionDTO to CollectionCreateDTO.

        :return CollectionCreateDTO: Converted CollectionCreateDTO instance.
        """
        return CollectionCreateDTO(
            import_id=self.import_id,
            title=self.title,
            description=self.description,
        )

    def to_collection_write_dto(self) -> CollectionWriteDTO:
        """
        Convert BulkImportCollectionDTO to CollectionWriteDTO.

        :return CollectionWriteDTO: Converted CollectionWriteDTO instance.
        """
        return CollectionWriteDTO(
            title=self.title, description=self.description, organisation=""
        )


class BulkImportFamilyDTO(BaseModel):
    """Representation of a family for bulk import."""

    import_id: str
    title: str
    summary: str
    geographies: list[str]
    category: str
    metadata: Metadata
    collections: list[str]
    corpus_import_id: str

    def to_family_create_dto(self, corpus_import_id: str) -> FamilyCreateDTO:
        """
        Convert BulkImportFamilyDTO to FamilyCreateDTO.

        :return FamilyCreateDTO: Converted FamilyCreateDTO instance.
        """
        return FamilyCreateDTO(
            import_id=self.import_id,
            title=self.title,
            summary=self.summary,
            geography=self.geographies,
            geographies=self.geographies,
            category=self.category,
            metadata=self.metadata.model_dump(),
            collections=self.collections,
            corpus_import_id=corpus_import_id,
        )

    def to_family_write_dto(self) -> FamilyWriteDTO:
        """
        Convert BulkImportFamilyDTO to FamilyWriteDTO.

        :return FamilyWriteDTO: Converted FamilyWriteDTO instance.
        """
        return FamilyWriteDTO(
            title=self.title,
            summary=self.summary,
            geographies=self.geographies,
            category=self.category,
            metadata=self.metadata.model_dump(),
            collections=self.collections,
        )


class BulkImportEventDTO(BaseModel):
    """Representation of an event for bulk import."""

    import_id: str
    family_import_id: str
    family_document_import_id: Optional[str] = None
    event_title: str
    date: datetime
    event_type_value: str

    def to_event_create_dto(self) -> EventCreateDTO:
        """
        Convert BulkImportEventDTO to EventCreateDTO.

        :return EventCreateDTO: Converted EventCreateDTO instance.
        """
        return EventCreateDTO(
            import_id=self.import_id,
            family_import_id=self.family_import_id,
            event_title=self.event_title,
            date=self.date,
            event_type_value=self.event_type_value,
        )


class BulkImportDocumentDTO(BaseModel):
    """Representation of a document for bulk import."""

    import_id: str
    family_import_id: str
    variant_name: Optional[str] = None
    metadata: Metadata
    title: str
    source_url: Optional[AnyHttpUrl] = None
    user_language_name: Optional[str] = None

    def to_document_create_dto(self) -> DocumentCreateDTO:
        """
        Convert BulkImportDocumentDTO to DocumentCreateDTO.

        :return DocumentCreateDTO: Converted DocumentCreateDTO instance.
        """

        return DocumentCreateDTO(
            import_id=self.import_id,
            family_import_id=self.family_import_id,
            variant_name=self.variant_name,
            metadata=self.metadata.model_dump(),
            title=self.title,
            source_url=self.source_url,
            user_language_name=self.user_language_name,
        )
