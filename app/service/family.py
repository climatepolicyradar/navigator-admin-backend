"""
Family Service

This file hands off to the family repo, adding the dependency of the db (future)
"""
import logging
from typing import Optional
from app.errors.repository_error import RepositoryError
from app.model.family import FamilyDTO
import app.repository.family as family_repo
import app.db.session as db_session
from sqlalchemy import exc

from app.service import id


_LOGGER = logging.getLogger(__name__)


def get(import_id: str) -> Optional[FamilyDTO]:
    """
    Gets a family given the import_id.

    :param str import_id: The import_id to use to get the family.
    :raises RepositoryError: raised on a database error.
    :raises ValidationError: raised should the import_id be invalid.
    :return Optional[FamilyDTO]: The family found or None.
    """
    id.validate(import_id)
    try:
        db = db_session.get_db()
        return family_repo.get(db, import_id)
    except exc.SQLAlchemyError as e:
        _LOGGER.error(e)
        raise RepositoryError(str(e))


def all() -> list[FamilyDTO]:
    db = db_session.get_db()
    return family_repo.all(db)


def search(search_term: str) -> list[FamilyDTO]:
    db = db_session.get_db()
    return family_repo.search(db, search_term)


def update(family: FamilyDTO) -> Optional[FamilyDTO]:
    db = db_session.get_db()
    return family_repo.update(db, family)


def create(family: FamilyDTO) -> Optional[FamilyDTO]:
    db = db_session.get_db()
    return family_repo.create(db, family)


def delete(import_id: str) -> bool:
    db = db_session.get_db()
    return family_repo.delete(db, import_id)
