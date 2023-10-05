from app.model.collection import CollectionReadDTO, CollectionWriteDTO


def create_collection_dto(
    import_id: str, title: str = "title", description="description"
) -> CollectionReadDTO:
    return CollectionReadDTO(
        import_id=import_id,
        title=title,
        description=description,
        families=[],
        organisation="CCLW",
    )


def create_write_collection_dto(
    title: str = "title", description="description"
) -> CollectionWriteDTO:
    return CollectionWriteDTO(
        title=title,
        description=description,
        organisation="CCLW",
    )
