from app.model.collection import (
    CollectionReadDTO,
    CollectionWriteDTO,
    CollectionCreateDTO,
)


def create_collection_read_dto(
    import_id: str, title: str = "title", description="description"
) -> CollectionReadDTO:
    return CollectionReadDTO(
        import_id=import_id,
        title=title,
        description=description,
        families=[],
        organisation="CCLW",
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
    title: str = "title", description="description"
) -> CollectionCreateDTO:
    return CollectionCreateDTO(
        title=title,
        description=description,
    )
