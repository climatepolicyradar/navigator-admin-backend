import logging
from typing import Optional, cast

from db_client.models.organisation.users import Organisation
from sqlalchemy.exc import MultipleResultsFound
from sqlalchemy.orm import Session
from sqlalchemy.sql import asc

from app.errors import RepositoryError
from app.model.organisation import OrganisationReadDTO

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
        description=str(org.description),
        type=str(org.organisation_type),
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
        _LOGGER.info(db.query(Organisation).all())
        org = db.query(Organisation).filter(Organisation.id == org_id).one_or_none()

    except MultipleResultsFound as e:
        _LOGGER.error(e)
        raise RepositoryError(e)

    return _org_to_dto(org) if org is not None else None


def get_by_name(db: Session, org_name: str) -> Optional[OrganisationReadDTO]:
    """Get an organisation from the database given a name.

    :param db Session: The database connection.
    :param str org_name: The name of the organisation to retrieve.
    :return Optional[OrganisationReadDTO]: The requested org or None.
    :raises RepositoryError: If there is an error during query.
    """
    try:
        org = db.query(Organisation).filter(Organisation.name == org_name).one_or_none()

    except MultipleResultsFound as e:
        _LOGGER.error(e)
        raise RepositoryError(e)

    return _org_to_dto(org) if org is not None else None
