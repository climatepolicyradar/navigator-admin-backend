from app.model.collection import CollectionReadDTO, CollectionWriteDTO


def create_collection_dto(
    import_id: str, title: str = "title", description="description"
) -> CollectionReadDTO:
    return CollectionReadDTO(
        import_id=import_id,
        title=title,
        description=description,
        families=[],
        organisation="test_org",
    )


def create_write_collection_dto(
    import_id: str, title: str = "title", description="description"
) -> CollectionWriteDTO:
    return CollectionWriteDTO(
        import_id=import_id,
        title=title,
        description=description,
        organisation="test_org",
    )
