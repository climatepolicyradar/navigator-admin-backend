from typing import Optional, Tuple, cast
from sqlalchemy.orm import Session

from app.clients.db.models.app.users import AppUser, Organisation, OrganisationUser

MaybeAppUser = Optional[AppUser]


def get_user_by_email(db: Session, email: str) -> MaybeAppUser:
    return db.query(AppUser).filter(AppUser.email == email).one()


def get_app_user_authorisation(
    db: Session, app_user: AppUser
) -> list[Tuple[OrganisationUser, Organisation]]:
    query = (
        db.query(OrganisationUser, Organisation)
        .filter(OrganisationUser.appuser_email == app_user.email)
        .join(Organisation, Organisation.id == OrganisationUser.organisation_id)
    )
    return [(r[0], r[1]) for r in query.all()]


def get_org_id(db: Session, user_email: str) -> Optional[int]:
    """Gets the organisation id given the user's email"""
    result = (
        db.query(Organisation.id)
        .select_from(Organisation)
        .join(OrganisationUser, Organisation.id == OrganisationUser.organisation_id)
        .join(AppUser, AppUser.email == user_email)
        .filter(AppUser.email == OrganisationUser.appuser_email)
        .scalar()
    )
    if result is not None:
        return cast(int, result)
