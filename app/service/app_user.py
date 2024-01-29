from sqlalchemy.orm import Session
from app.clients.db.errors import ValidationError
from app.repository import app_user_repo


def get_organisation(db: Session, user_email: str) -> int:
    """Gets a user's organisation"""
    org_id = app_user_repo.get_org_id(db, user_email)
    if org_id is None:
        raise ValidationError(f"Could not get the organisation for user {user_email}")
    return org_id
