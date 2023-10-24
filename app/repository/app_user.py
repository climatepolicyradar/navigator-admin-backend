from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.clients.db.models.app.users import AppUser, Organisation, OrganisationUser

MaybeAppUser = Optional[AppUser]


def get_user_by_email(db: Session, email: str) -> MaybeAppUser:
    return db.query(AppUser).filter(AppUser.email == email).one()


def is_active(db: Session, email: str) -> bool:
    return (
        db.query(OrganisationUser)
        .filter(OrganisationUser.appuser_email == email)
        .filter(OrganisationUser.is_active is True)
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
