from typing import Optional, Tuple, cast

from db_client.models.organisation import AppUser, Organisation, OrganisationUser
from sqlalchemy.orm import Session

from app.model.user import OrgMembership, UserReadDTO

MaybeAppUser = Optional[AppUser]


def get_user_by_email(db: Session, email: str) -> MaybeAppUser:
    return db.query(AppUser).filter(AppUser.email == email).one()


def is_superuser(db: Session, email: str) -> bool:
    """Check whether user with email address is a superuser.

    :param db Session: DB session to connect use.
    :param email str: User email.
    :return bool: Whether the user is a superuser or not.
    """
    return (
        db.query(AppUser)
        .filter(AppUser.email == email)
        .filter(AppUser.is_superuser == True)  # noqa: E712
        .count()
        > 0
    )


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


def get_user(db: Session, email: str) -> Optional[UserReadDTO]:
    """Get a user and their organisation memberships by email."""
    user = db.query(AppUser).filter(AppUser.email == email).one_or_none()
    if user is None:
        return None
    org_links = (
        db.query(OrganisationUser).filter(OrganisationUser.appuser_email == email).all()
    )
    return UserReadDTO(
        email=cast(str, user.email),
        name=cast(str, user.name) if user.name else None,
        is_superuser=cast(bool, user.is_superuser),
        organisations=[
            OrgMembership(
                id=cast(int, link.organisation_id), is_admin=cast(bool, link.is_admin)
            )
            for link in org_links
        ],
    )


def all_users(db: Session) -> list[UserReadDTO]:
    """Get all users with their organisation memberships."""
    users = db.query(AppUser).order_by(AppUser.email).all()
    return [
        u for u in (get_user(db, cast(str, u.email)) for u in users) if u is not None
    ]


def update_org_memberships(
    db: Session, email: str, organisations: list[OrgMembership]
) -> None:
    """Replace a user's organisation memberships with the provided list."""
    db.query(OrganisationUser).filter(OrganisationUser.appuser_email == email).delete()
    for org in organisations:
        db.add(
            OrganisationUser(
                appuser_email=email,
                organisation_id=org.id,
                job_title="",
                is_active=True,
                is_admin=org.is_admin,
            )
        )

    db.flush()
