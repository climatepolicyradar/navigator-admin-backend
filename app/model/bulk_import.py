import logging
import os
from datetime import datetime
from pprint import pformat
from typing import Any, Optional, Union

from pydantic import AnyHttpUrl, BaseModel, RootModel, model_validator

from app.model.collection import CollectionCreateDTO, CollectionWriteDTO
from app.model.document import DocumentCreateDTO, DocumentWriteDTO
from app.model.event import EventCreateDTO, EventWriteDTO
from app.model.family import FamilyCreateDTO, FamilyWriteDTO

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())


class Metadata(RootModel[dict[str, Union[str, list[str]]]]):
    @model_validator(mode="after")
    def _sort(self) -> "Metadata":
        ordered: dict[str, Union[str, list[str]]] = {}
        for key in self.root.keys():
            value = self.root[key]
            if isinstance(value, list):
                ordered[key] = sorted(value)
            else:
                ordered[key] = value
        self.root = ordered
        return self


class BulkImportCollectionDTO(BaseModel):
    """Representation of a collection for bulk import."""

    import_id: str
    title: str
    description: str
    metadata: Metadata

    def to_collection_create_dto(self) -> CollectionCreateDTO:
        """
        Convert BulkImportCollectionDTO to CollectionCreateDTO.

        :return CollectionCreateDTO: Converted CollectionCreateDTO instance.
        """
        return CollectionCreateDTO(
            import_id=self.import_id,
            title=self.title,
            description=self.description,
            metadata=self.metadata.model_dump(),
        )

    def to_collection_write_dto(self) -> CollectionWriteDTO:
        """
        Convert BulkImportCollectionDTO to CollectionWriteDTO.

        :return CollectionWriteDTO: Converted CollectionWriteDTO instance.
        """
        return CollectionWriteDTO(
            title=self.title,
            description=self.description,
            metadata=self.metadata.model_dump(),
            organisation="",
        )

    def is_different_from(self, collection):
        """Check if this DTO is different from another DTO"""
        comparison_dto = BulkImportCollectionDTO(
            import_id=collection.import_id,
            title=collection.title,
            description=collection.description,
            metadata=collection.metadata,
        )

        keys = set(self.__class__.model_fields.keys())
        is_different = self.model_dump(include=keys) != comparison_dto.model_dump(
            include=keys
        )

        if is_different:
            log_differences(self, comparison_dto, keys)

        return is_different


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
    concepts: Optional[list[dict[str, Any]]] = []

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
            concepts=self.concepts,
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
            concepts=self.concepts,
        )

    def is_different_from(self, family):
        """Check if this DTO is different from another DTO"""
        comparison_dto = BulkImportFamilyDTO(
            import_id=family.import_id,
            title=family.title,
            summary=family.summary,
            geographies=sorted(family.geographies),
            category=family.category,
            metadata=family.metadata,
            collections=sorted(family.collections),
            corpus_import_id=family.corpus_import_id,
            concepts=sorted(
                family.concepts or [], key=lambda x: (x["relation"], x["id"])
            ),
        )

        self.collections = sorted(self.collections)
        self.geographies = sorted(self.geographies)
        self.concepts = sorted(
            self.concepts or [], key=lambda x: (x["relation"], x["id"])
        )

        keys = set(self.__class__.model_fields.keys())
        is_different = self.model_dump(include=keys) != comparison_dto.model_dump(
            include=keys
        )

        if is_different:
            log_differences(self, comparison_dto, keys)

        return is_different


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

    def to_document_write_dto(self) -> DocumentWriteDTO:
        """
        Convert BulkImportDocumentDTO to DocumentWriteDTO.

        :return DocumentWriteDTO: Converted DocumentWriteDTO instance.
        """
        return DocumentWriteDTO(
            variant_name=self.variant_name,
            metadata=self.metadata.model_dump(),
            title=self.title,
            source_url=self.source_url,
            user_language_name=self.user_language_name,
        )

    def is_different_from(self, document):
        """Check if this DTO is different from another DTO"""
        comparison_dto = BulkImportDocumentDTO(
            import_id=document.import_id,
            family_import_id=document.family_import_id,
            title=document.title,
            variant_name=document.variant_name,
            metadata=document.metadata,
            source_url=document.source_url,
            user_language_name=document.user_language_name,
        )

        keys = set(self.__class__.model_fields.keys())
        if self.user_language_name is None:
            keys.remove("user_language_name")

        is_different = self.model_dump(include=keys) != comparison_dto.model_dump(
            include=keys
        )

        if is_different:
            log_differences(self, comparison_dto, keys)

        return is_different


class BulkImportEventDTO(BaseModel):
    """Representation of an event for bulk import."""

    import_id: str
    family_import_id: str
    family_document_import_id: Optional[str] = None
    event_title: str
    date: datetime
    event_type_value: str
    metadata: Metadata

    def to_event_create_dto(self) -> EventCreateDTO:
        """
        Convert BulkImportEventDTO to EventCreateDTO.

        :return EventCreateDTO: Converted EventCreateDTO instance.
        """
        return EventCreateDTO(
            import_id=self.import_id,
            family_import_id=self.family_import_id,
            family_document_import_id=self.family_document_import_id,
            event_title=self.event_title,
            date=self.date,
            event_type_value=self.event_type_value,
            metadata=self.metadata.model_dump(),
        )

    def to_event_write_dto(self) -> EventWriteDTO:
        """
        Convert BulkImportEventDTO to EventWriteDTO.

        :return EventWriteDTO: Converted EventWriteDTO instance.
        """
        return EventWriteDTO(
            event_title=self.event_title,
            date=self.date,
            event_type_value=self.event_type_value,
            metadata=self.metadata.model_dump(),
            family_document_import_id=self.family_document_import_id,
        )

    def is_different_from(self, event, event_metadata):
        """Check if this DTO is different from another DTO"""
        comparison_dto = BulkImportEventDTO(
            import_id=event.import_id,
            family_import_id=event.family_import_id,
            family_document_import_id=event.family_document_import_id,
            event_title=event.event_title,
            date=event.date.replace(tzinfo=None),
            event_type_value=event.event_type_value,
            metadata=event_metadata,
        )

        keys = set(self.__class__.model_fields.keys())
        is_different = self.model_dump(include=keys) != comparison_dto.model_dump(
            include=keys
        )

        if is_different:
            log_differences(self, comparison_dto, keys)

        return is_different


def log_differences(update_dto: BaseModel, current_dto: BaseModel, keys: set) -> None:
    """
    Log the differences between two DTOs.

    :param BaseModel current_dto: The current DTO.
    :param BaseModel comparison_dto: The DTO to compare with.
    :param set keys: The keys to compare.
    """
    for key in keys:
        update_value = getattr(update_dto, key)
        current_value = getattr(current_dto, key)
        if update_value != current_value:
            current_formatted = pformat(current_value)
            update_formatted = pformat(update_value)

            current_lines = current_formatted.split("\n")
            current_colored = "\n".join(
                f"\033[91m{line}\033[0m" for line in current_lines
            )

            update_lines = update_formatted.split("\n")
            update_colored = "\n".join(
                f"\033[92m{line}\033[0m" for line in update_lines
            )

            _LOGGER.info(
                f"\033[94m🔀 Change detected in `{key}`:\033[0m\n"
                f"🟡 Before:\n{current_colored}\n"
                f"🟢 After:\n{update_colored}"
            )
