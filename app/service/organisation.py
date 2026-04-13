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
    Create an organisation and ensure it has an ``entity_counter`` row.

    Import-id generation depends on that row; the service orchestrates
    persistence after the core insert.

    :param organisation: Payload for the new organisation.
    :type organisation: OrganisationCreateDTO
    :raises RepositoryError: If raised by lower layers (propagated).
    :return: Database id of the new organisation row.
    :rtype: int
    """
    with db_session.get_db() as db:
        try:
            org_id = organisation_repo.create(db, organisation)
            organisation_repo.ensure_entity_counter_for_organisation(
                db, organisation.internal_name
            )
            return org_id
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
    Update an organisation; ensure ``entity_counter`` exists when found.

    Backfills a missing counter even when the UPDATE is a no-op so legacy
    rows are repaired on save.

    :param id: Primary key of the organisation.
    :type id: int
    :param organisation: Replacement field values.
    :type organisation: OrganisationWriteDTO
    :raises Exception: Database or repository failures.
    :return: The updated DTO, or ``None`` if the id does not exist.
    :rtype: Optional[OrganisationReadDTO]
    """
    with db_session.get_db() as db:
        try:
            outcome = organisation_repo.update(db, id, organisation)
            if outcome is None:
                db.rollback()
            else:
                organisation_repo.ensure_entity_counter_for_organisation(
                    db, organisation.internal_name
                )
                db.commit()
        except Exception as e:
            db.rollback()
            raise e

        return get(id, db)
