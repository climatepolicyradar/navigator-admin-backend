from app.service.collection import validate_import_id


def validate_collection(collection: dict) -> None:
    validate_import_id(collection["import_id"])
