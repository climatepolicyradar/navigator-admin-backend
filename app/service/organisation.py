from sqlalchemy.orm import Session
from app.errors.validation_error import ValidationError
import app.repository.organisation as org_repo


def validate(db: Session, org_name: str) -> int:
    id = org_repo.get_id_from_name(db, org_name)
    if id is None:
        raise ValidationError(f"The organisation name {org_name} is invalid!")
    return id
