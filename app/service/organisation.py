from typing import Optional

from pydantic import ConfigDict, validate_call
from sqlalchemy.orm import Session

import app.clients.db.session as db_session
from app.errors import ValidationError
from app.model.organisation import (
    OrganisationCreateDTO,
    OrganisationReadDTO,
    OrganisationWriteDTO,
)
from app.repository import organisation as organisation_repo


def get_id_from_name(db: Session, org_name: str) -> int:
    id = organisation_repo.get_id_from_name(db, org_name)
    if id is None:
        raise ValidationError(f"The organisation name {org_name} is invalid!")
    return id


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def all() -> list[OrganisationReadDTO]:
    """Get the entire list of organisations from the repository.

    :return list[OrganisationReadDTO]: The list of organisations.
    """
    with db_session.get_db() as db:
        return organisation_repo.all(db)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def get(
    organisation: int, db: Optional[Session] = None
) -> Optional[OrganisationReadDTO]:
    """Retrieve an organisation by ID or name.

    :param int organisation: The ID of an organisation to retrieve.
    :return OrganisationReadDTO: The requested organisation.
    :raises RepositoryError: If there is an error during retrieval.
    """
    if db is None:
        with db_session.get_db() as session:
            return get(organisation, session)

    return organisation_repo.get_by_id(db, organisation)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def create(organisation: OrganisationCreateDTO) -> int:
    """
    Creates a new organisation with the values passed.

    :param OrganisationCreateDTO organisation: The values for the new organisation to create.
    :raises RepositoryError: If there is an error during creation.
    :return int: The id of the newly created organisation.
    """
    with db_session.get_db() as db:
        try:
            return organisation_repo.create(db, organisation)
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.commit()


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def update(
    id: int, organisation: OrganisationWriteDTO
) -> Optional[OrganisationReadDTO]:
    """
    Updates an existing organisation with the values passed.

    :param int id: The id of the existing organisation to be updated.
    :param OrganisationWriteDTO organisation: The values for updating an existing organisation.
    :raises Exception: If there is an error during the update.
    :return OrganisationReadDTO: The updated organisation.
    """
    with db_session.get_db() as db:
        try:
            if organisation_repo.update(db, id, organisation):
                db.commit()
            else:
                db.rollback()
        except Exception as e:
            db.rollback()
            raise e

        return get(id, db)
