from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.clients.db.models.app.users import AppUser, Organisation, OrganisationUser

MaybeAppUser = Optional[AppUser]


def get_user_by_email(db: Session, email: str) -> MaybeAppUser:
    return db.query(AppUser).filter(AppUser.email == email).one()


def get_app_user_authorisation(
    db: Session, app_user: AppUser
) -> list[Tuple[OrganisationUser, Organisation]]:
    return (
        db.query(OrganisationUser, Organisation)
        .filter(OrganisationUser.appuser_email == app_user.email)
        .join(Organisation, Organisation.id == OrganisationUser.organisation_id)
        .all()
    )
