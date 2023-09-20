"""
Family Service

This file hands off to the family repo, adding the dependency of the db (future)
"""
import logging
from typing import Optional

from pydantic import ConfigDict, validate_call
from app.errors import RepositoryError
from app.model.family import FamilyReadDTO, FamilyWriteDTO
import app.clients.db.session as db_session
from sqlalchemy import exc
from sqlalchemy.orm import Session

from app.service import id
from app.service import geography
from app.service import category
from app.service import organisation
from app.service import metadata

from app.repository import family_repo

_LOGGER = logging.getLogger(__name__)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def get(import_id: str) -> Optional[FamilyReadDTO]:
    """
    Gets a family given the import_id.

    :param str import_id: The import_id to use to get the family.
    :raises RepositoryError: raised on a database error.
    :raises ValidationError: raised should the import_id be invalid.
    :return Optional[FamilyDTO]: The family found or None.
    """
    validate_import_id(import_id)
    try:
        with db_session.get_db() as db:
            return family_repo.get(db, import_id)
    except exc.SQLAlchemyError as e:
        _LOGGER.error(e)
        raise RepositoryError(str(e))


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def all() -> list[FamilyReadDTO]:
    """
    Gets the entire list of families from the repository.

    :return list[FamilyDTO]: The list of families.
    """
    with db_session.get_db() as db:
        return family_repo.all(db)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def search(search_term: str) -> list[FamilyReadDTO]:
    """
    Searches the title and descriptions of all the Families for the search term.

    :param str search_term: Search pattern to match.
    :return list[FamilyDTO]: The list of families matching the search term.
    """
    with db_session.get_db() as db:
        return family_repo.search(db, search_term)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def validate_import_id(import_id: str) -> None:
    """
    Validates the import id for a family.

    TODO: add more validation

    :param str import_id: import id to check.
    :raises ValidationError: raised should the import_id be invalid.
    """
    id.validate(import_id)


@db_session.with_transaction(__name__)
@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def update(
    family: FamilyWriteDTO, db: Session = db_session.get_db()
) -> Optional[FamilyReadDTO]:
    """
    Updates a single Family with the values passed.

    :param FamilyDTO family: The DTO with all the values to change (or keep).
    :raises RepositoryError: raised on a database error.
    :raises ValidationError: raised should the import_id be invalid.
    :return Optional[FamilyDTO]: The updated Family or None if not updated.
    """
    validate_import_id(family.import_id)
    category.validate(family.category)
    org_id = organisation.get_id(db, family.organisation)
    metadata.validate(db, org_id, family.metadata)
    geo_id = geography.get_id(db, family.geography)

    if family_repo.update(db, family, geo_id):
        db.commit()
        return get(family.import_id)


@db_session.with_transaction(__name__)
@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def create(
    family: FamilyWriteDTO, db: Session = db_session.get_db()
) -> Optional[FamilyReadDTO]:
    """
    Creates a new Family with the values passed.

    :param FamilyDTO family: The values for the new Family.
    :raises RepositoryError: raised on a database error
    :raises ValidationError: raised should the import_id be invalid.
    :return Optional[FamilyDTO]: The new created Family or None if unsuccessful.
    """
    id.validate(family.import_id)
    geo_id = geography.get_id(db, family.geography)
    category.validate(family.category)
    org_id = organisation.get_id(db, family.organisation)
    metadata.validate(db, org_id, family.metadata)

    if family_repo.create(db, family, geo_id, org_id):
        db.commit()
        return get(family.import_id)


@db_session.with_transaction(__name__)
@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def delete(import_id: str, db: Session = db_session.get_db()) -> bool:
    """
    Deletes the Family specified by the import_id.

    :param str import_id: The import_id of the Family to delete.
    :raises RepositoryError: raised on a database error.
    :raises ValidationError: raised should the import_id be invalid.
    :return bool: True if deleted else False.
    """
    id.validate(import_id)
    return family_repo.delete(db, import_id)
