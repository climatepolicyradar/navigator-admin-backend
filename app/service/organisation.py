import logging
from typing import Optional

from pydantic import ConfigDict, validate_call
from sqlalchemy.orm import Session

import app.clients.db.session as db_session
from app.errors import ValidationError
from app.model.organisation import OrganisationReadDTO
from app.repository import organisation as organisation_repo

_LOGGER = logging.getLogger(__name__)


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
        db = db_session.get_db()

    return organisation_repo.get_by_id(db, organisation)
