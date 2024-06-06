import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.errors import AuthorisationError, ValidationError
from app.repository import app_user_repo

_LOGGER = logging.getLogger(__name__)


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
    org_id = get_organisation(db, user_email)
    superuser: bool = is_superuser(db, user_email)
    if superuser:
        _LOGGER.error("IS SUPERUSER")
        return None
    _LOGGER.error("ORG ID: %s", org_id)
    return org_id


def is_authorised_to_make_changes(
    db, user_email: str, entity_org_id: int, import_id: str
) -> bool:
    """Validate entity belongs to same org as current user."""

    user_org_id = restrict_entities_to_user_org(db, user_email)
    if user_org_id is None:
        return True

    if entity_org_id != user_org_id:
        msg = f"User '{user_email}' is not authorised to perform operation on '{import_id}'"
        raise AuthorisationError(msg)

    return bool(entity_org_id == user_org_id)
