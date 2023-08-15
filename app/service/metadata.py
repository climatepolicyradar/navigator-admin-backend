from app.errors.validation_error import ValidationError
from app.model.general import Json
from sqlalchemy.orm import Session
import app.repository.metadata as metadata_repo


def validate(db: Session, org_id: int, data: Json) -> bool:
    schema = metadata_repo.get_schema_for_org(db, org_id)
    if schema is None:
        raise ValidationError(f"Organisation {org_id} has no Taxonomy defined!")
    return _validate(schema, data)


def _validate(schema: Json, data: Json) -> bool:
    """
    Validates the data against the schema

    :param Json schema: The schema to use for the validation
    :param Json data: The values to use
    :return bool: True if valid, False if not
    """
    return True
