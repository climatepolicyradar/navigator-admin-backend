from typing import Optional

from sqlalchemy.orm import Session

from app.errors import ValidationError
from app.repository import app_user_repo


def get_organisation(db: Session, user_email: str) -> int:
    """Gets a user's organisation"""
    org_id = app_user_repo.get_org_id(db, user_email)
    if org_id is None:
        raise ValidationError(f"Could not get the organisation for user {user_email}")
    return org_id


def is_superuser(db: Session, user_email: str) -> bool:
    """Determine a user's superuser status"""
    return app_user_repo.is_superuser(db, user_email)


def restrict_entities_to_user_org(db: Session, user_email: str) -> Optional[int]:
    superuser: bool = is_superuser(db, user_email)
    if superuser:
        return None
    return get_organisation(db, user_email)
