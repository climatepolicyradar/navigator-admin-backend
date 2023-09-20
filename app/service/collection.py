"""
Collection Service

This layer uses the collection repo to handle storage management and other
services for validation etc.
"""
import logging
from typing import Optional

from pydantic import ConfigDict, validate_call
from app.errors import RepositoryError
from app.model.collection import CollectionReadDTO, CollectionWriteDTO
from app.repository import collection_repo
import app.clients.db.session as db_session
from sqlalchemy import exc
from sqlalchemy.orm import Session

from app.service import id
from app.service import organisation


_LOGGER = logging.getLogger(__name__)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def get(import_id: str) -> Optional[CollectionReadDTO]:
    """
    Gets a collection given the import_id.

    :param str import_id: The import_id to use to get the collection.
    :raises RepositoryError: raised on a database error.
    :raises ValidationError: raised should the import_id be invalid.
    :return Optional[CollectionDTO]: The collection found or None.
    """
    validate_import_id(import_id)
    try:
        with db_session.get_db() as db:
            return collection_repo.get(db, import_id)
    except exc.SQLAlchemyError as e:
        _LOGGER.error(e)
        raise RepositoryError(str(e))


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def all() -> list[CollectionReadDTO]:
    """
    Gets the entire list of collections from the repository.

    :return list[CollectionDTO]: The list of collections.
    """
    with db_session.get_db() as db:
        return collection_repo.all(db)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def search(search_term: str) -> list[CollectionReadDTO]:
    """
    Searches the title and descriptions of all the collections for the search term.

    :param str search_term: Search pattern to match.
    :return list[CollectionDTO]: The list of collections matching the search term.
    """
    with db_session.get_db() as db:
        return collection_repo.search(db, search_term)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def validate_import_id(import_id: str) -> None:
    """
    Validates the import id for a collection.

    TODO: add more validation

    :param str import_id: import id to check.
    :raises ValidationError: raised should the import_id be invalid.
    """
    id.validate(import_id)


@db_session.with_transaction(__name__)
@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def update(
    collection: CollectionWriteDTO, db: Session = db_session.get_db()
) -> Optional[CollectionReadDTO]:
    """
    Updates a single collection with the values passed.

    :param CollectionDTO collection: The DTO with all the values to change (or keep).
    :raises RepositoryError: raised on a database error.
    :raises ValidationError: raised should the import_id be invalid.
    :return Optional[CollectionDTO]: The updated collection or None if not updated.
    """
    validate_import_id(collection.import_id)

    # TODO: implement changing of a collection's organisation
    # org_id = organisation.get_id(db, collection.organisation)

    if collection_repo.update(db, collection):
        db.commit()
        return get(collection.import_id)


@db_session.with_transaction(__name__)
@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def create(
    collection: CollectionWriteDTO, db: Session = db_session.get_db()
) -> Optional[CollectionReadDTO]:
    """
        Creates a new collection with the values passed.

        :param CollectionDTO collection: The values for the new collection.
        :raises RepositoryError: raised on a database error
        :raises ValidationError: raised should the import_id be invalid.
        :return Optional[CollectionDTO]: The new created collection or
    None if unsuccessful.
    """
    id.validate(collection.import_id)
    org_id = organisation.get_id(db, collection.organisation)

    if collection_repo.create(db, collection, org_id):
        db.commit()
        return get(collection.import_id)


@db_session.with_transaction(__name__)
@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def delete(import_id: str, db: Session = db_session.get_db()) -> bool:
    """
    Deletes the collection specified by the import_id.

    :param str import_id: The import_id of the collection to delete.
    :raises RepositoryError: raised on a database error.
    :raises ValidationError: raised should the import_id be invalid.
    :return bool: True if deleted else False.
    """
    id.validate(import_id)
    return collection_repo.delete(db, import_id)
