import logging
from typing import Optional

from db_client.models.organisation import AppUser
from sqlalchemy import update as db_update
from sqlalchemy.orm import Session

import app.clients.db.session as db_session
import app.repository.organisation as org_repo
from app.errors import AuthorisationError, ValidationError
from app.model.user import UserContext, UserReadDTO, UserWriteDTO
from app.repository import app_user_repo

_LOGGER = logging.getLogger(__name__)


def is_superuser(db: Session, user: UserContext) -> bool:
    """Determine a user's superuser status"""
    return app_user_repo.is_superuser(db, user.email)


def restrict_entities_to_user_org(user: UserContext) -> Optional[list[int]]:
    if user.is_superuser:
        return None
    return user.org_ids


def all_users() -> list[UserReadDTO]:
    """Return all users with their organisation memberships."""
    with db_session.get_db() as db:
        return app_user_repo.all_users(db)


def get_user(email: str) -> Optional[UserReadDTO]:
    """Return a single user by email, or None if not found."""
    with db_session.get_db() as db:
        return app_user_repo.get_user(db, email)


def update_user(email: str, user_write: UserWriteDTO) -> Optional[UserReadDTO]:
    """Update a user's name and organisation memberships.

    Validates all supplied org IDs exist, then replaces the user's memberships.
    """
    with db_session.get_db() as db:
        existing = app_user_repo.get_user(db, email)
        if existing is None:
            return None

        for org in user_write.organisations:
            if org_repo.get_name_from_id(db, org.id) is None:
                raise ValidationError(f"Organisation {org.id} not found")

        if user_write.name is not None:
            db.execute(
                db_update(AppUser)
                .where(AppUser.email == email)
                .values(name=user_write.name)
            )

        app_user_repo.update_org_memberships(db, email, user_write.organisations)
        db.commit()

        return app_user_repo.get_user(db, email)


def raise_if_unauthorised_to_make_changes(
    user: UserContext, entity_org_id: int, import_id: str
) -> bool:
    """Validate entity belongs to one of the user's accessible orgs."""
    if user.is_superuser:
        return True

    accessible = restrict_entities_to_user_org(user) or []
    if entity_org_id not in accessible:
        msg = f"User '{user.email}' is not authorised to perform operation on '{import_id}'"
        _LOGGER.error(msg)
        raise AuthorisationError(msg)

    return True
