import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.errors import AuthorisationError
from app.model.jwt_user import UserContext
from app.repository import app_user_repo

_LOGGER = logging.getLogger(__name__)


def is_superuser(db: Session, user: UserContext) -> bool:
    """Determine a user's superuser status"""
    return app_user_repo.is_superuser(db, user.email)


def restrict_entities_to_user_org(user: UserContext) -> Optional[int]:
    if user.is_superuser:
        return None
    return user.org_id


def raise_if_unauthorised_to_make_changes(
    user: UserContext, entity_org_id: int, import_id: str
) -> bool:
    """Validate entity belongs to same org as current user."""
    if user.is_superuser:
        return True

    if entity_org_id != user.org_id:
        msg = f"User '{user.email}' is not authorised to perform operation on '{import_id}'"
        _LOGGER.error(msg)
        raise AuthorisationError(msg)

    return bool(entity_org_id == user.org_id)
