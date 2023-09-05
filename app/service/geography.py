from sqlalchemy.orm import Session
from app.errors import ValidationError
import app.repository.geography as geo_repo


def validate(db: Session, geo_string: str) -> int:
    id = geo_repo.get_id_from_value(db, geo_string)
    if id is None:
        raise ValidationError(f"The geography value {geo_string} is invalid!")
    return id
