from app.model.collection import CollectionDTO


def create_collection_dto(import_id: str) -> CollectionDTO:
    return CollectionDTO(
        import_id=import_id,
        title="title",
        description="description",
        families=[],
        organisation="org",
    )
