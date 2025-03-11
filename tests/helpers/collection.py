from datetime import datetime

from app.model.collection import (
    CollectionCreateDTO,
    CollectionReadDTO,
    CollectionWriteDTO,
)


def create_collection_read_dto(
    import_id: str, title: str = "title", description="description"
) -> CollectionReadDTO:
    return CollectionReadDTO(
        import_id=import_id,
        title=title,
        description=description,
        metadata={},
        families=[],
        organisation="CCLW",
        created=datetime.now(),
        last_modified=datetime.now(),
    )


def create_collection_write_dto(
    title: str = "title", description="description"
) -> CollectionWriteDTO:
    return CollectionWriteDTO(
        title=title,
        description=description,
        organisation="CCLW",
    )


def create_collection_create_dto(
    title: str = "title", description="description", metadata={}
) -> CollectionCreateDTO:
    return CollectionCreateDTO(title=title, description=description, metadata=metadata)
