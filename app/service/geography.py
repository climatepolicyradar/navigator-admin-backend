from sqlalchemy.orm import Session
from app.errors.validation_error import ValidationError
from app.repository.geography import get_id_from_value


def validate(db: Session, geo_string: str) -> int:
    id = get_id_from_value(db, geo_string)
    if id is None:
        raise ValidationError(f"The geography string {geo_string} is invalid!")
    return id
