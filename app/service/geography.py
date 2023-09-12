from sqlalchemy.orm import Session
from app.errors import ValidationError
from app.repository import geography_repo


def validate(db: Session, geo_string: str) -> int:
    id = geography_repo.get_id_from_value(db, geo_string)
    if id is None:
        raise ValidationError(f"The geography value {geo_string} is invalid!")
    return id
