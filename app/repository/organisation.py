import logging
from typing import Optional, cast

from db_client.models.organisation.users import Organisation
from sqlalchemy import update as db_update
from sqlalchemy.exc import MultipleResultsFound
from sqlalchemy.orm import Session
from sqlalchemy.sql import asc

from app.errors import RepositoryError
from app.model.organisation import (
    OrganisationCreateDTO,
    OrganisationReadDTO,
    OrganisationWriteDTO,
)

_LOGGER = logging.getLogger(__name__)


def get_id_from_name(db: Session, org_name: str) -> Optional[int]:
    return db.query(Organisation.id).filter_by(name=org_name).scalar()


def get_name_from_id(db: Session, org_id: int) -> Optional[str]:
    return db.query(Organisation.name).filter_by(id=org_id).scalar()


def get_distinct_org_options(db: Session) -> list[str]:
    query = db.query(Organisation).all()

    # Combine organisation_type values with name unique values into a single list.
    org_names = [org.name for org in query]
    org_types = [org.organisation_type for org in query]
    options = list(set(org_names + org_types))
    return options


def _org_to_dto(org: Organisation) -> OrganisationReadDTO:
    """Convert an Organisation model to a OrganisationReadDTO.

    :param Organisation org: The org model.
    :return OrganisationReadDTO: The corresponding DTO.
    """
    return OrganisationReadDTO(
        id=cast(int, org.id),
        internal_name=str(org.name),
        display_name=str(org.display_name),
        description=str(org.description) if org.description else "",
        type=str(org.organisation_type),
        attribution_url=str(org.attribution_url) if org.attribution_url else None,
    )


def all(db: Session) -> list[OrganisationReadDTO]:
    """Get a list of all corpus types in the database.

    :param db Session: The database connection.
    :return OrganisationReadDTO: The requested organisation.
    :raises RepositoryError: If the corpus type is not found.
    """
    query = db.query(Organisation)
    result = query.order_by(asc(Organisation.name)).all()

    if not result:
        return []

    return [_org_to_dto(org) for org in result]


def get_by_id(db: Session, org_id: int) -> Optional[OrganisationReadDTO]:
    """Get an organisation from the database given an ID.

    :param db Session: The database connection.
    :param int org_id: The ID of the organisation to retrieve.
    :return Optional[OrganisationReadDTO]: The requested org or None.
    :raises RepositoryError: If there is an error during query.
    """
    try:
        org = db.query(Organisation).filter(Organisation.id == org_id).one_or_none()

    except MultipleResultsFound as e:
        _LOGGER.error(e)
        raise RepositoryError(e)

    return _org_to_dto(org) if org is not None else None


def create(db: Session, organisation: OrganisationCreateDTO) -> int:
    """
    Creates a new organisation.

    :param db Session: The database connection.
    :param OrganisationCreateDTO collection: The values for the new organisation to be created.
    :raises RepositoryError: If an organisation could not be created.
    :return int: The id of the newly created organisation.
    """
    new_organisation = Organisation(
        name=organisation.internal_name,
        display_name=organisation.display_name,
        description=organisation.description,
        organisation_type=organisation.type,
        attribution_url=organisation.attribution_url,
    )

    db.add(new_organisation)
    db.flush()

    return int(getattr(new_organisation, "id"))


def update(db: Session, id: int, organisation: OrganisationWriteDTO) -> bool:
    """
    Updates an existing organisation.

    :param db Session: The database connection.
    :param int id: The id of the existing organisation to be updated.
    :param OrganisationWriteDTO collection: The values for updating an existing organisation.
    :raises RepositoryError: If an organisation could not be created.
    :return bool: True if new values were set otherwise false.
    """
    original_organisation = (
        db.query(Organisation).filter(Organisation.id == id).one_or_none()
    )

    if original_organisation is None:
        _LOGGER.error(f"Unable to find organisation for update: {id}")
        return False

    result = db.execute(
        db_update(Organisation)
        .where(Organisation.id == id)
        .values(
            name=organisation.internal_name,
            display_name=organisation.display_name,
            description=organisation.description,
            organisation_type=organisation.type,
            attribution_url=organisation.attribution_url,
        )
    )

    return True if result.rowcount != 0 else False  # type: ignore
