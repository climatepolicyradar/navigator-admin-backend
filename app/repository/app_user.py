from typing import Optional, Tuple, cast

from db_client.models.app.users import AppUser, Organisation, OrganisationUser
from sqlalchemy.orm import Session

MaybeAppUser = Optional[AppUser]


def get_user_by_email(db: Session, email: str) -> MaybeAppUser:
    return db.query(AppUser).filter(AppUser.email == email).one()


def is_active(db: Session, email: str) -> bool:
    # NOTE: DO NOT be tempted to fix the below to "is True" - this breaks things
    return (
        db.query(OrganisationUser)
        .filter(OrganisationUser.appuser_email == email)
        .filter(OrganisationUser.is_active == True)  # noqa: E712
        .count()
        > 0
    )


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
