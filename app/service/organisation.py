from sqlalchemy.orm import Session
from navigator_db_client.errors import ValidationError
from app.repository import organisation_repo


def get_id(db: Session, org_name: str) -> int:
    id = organisation_repo.get_id_from_name(db, org_name)
    if id is None:
        raise ValidationError(f"The organisation name {org_name} is invalid!")
    return id
