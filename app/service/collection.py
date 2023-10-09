"""
Collection Service

This layer uses the collection repo to handle storage management and other
services for validation etc.
"""
import logging
from typing import Optional

from pydantic import ConfigDict, validate_call
from app.errors import RepositoryError
from app.model.collection import (
    CollectionCreateDTO,
    CollectionReadDTO,
    CollectionWriteDTO,
)
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
    except exc.SQLAlchemyError:
        _LOGGER.exception(f"When getting collection {import_id}")
        raise RepositoryError(f"Error when getting collection {import_id}")


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def all() -> list[CollectionReadDTO]:
    """
    Gets the entire list of collections from the repository.

    :return list[CollectionDTO]: The list of collections.
    """
    try:
        with db_session.get_db() as db:
            return collection_repo.all(db)
    except exc.SQLAlchemyError:
        _LOGGER.exception("When getting all collections")
        raise RepositoryError("Error when getting all collection")


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def search(search_term: str) -> list[CollectionReadDTO]:
    """
    Searches the title and descriptions of all the collections for the search term.

    :param str search_term: Search pattern to match.
    :return list[CollectionDTO]: The list of collections matching the search term.
    """
    try:
        with db_session.get_db() as db:
            return collection_repo.search(db, search_term)
    except exc.SQLAlchemyError:
        _LOGGER.exception(f"When searching for collections with '{search_term}'")
        raise RepositoryError(f"When searching for collections with '{search_term}'")


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
    import_id: str, collection: CollectionWriteDTO, db: Session = db_session.get_db()
) -> Optional[CollectionReadDTO]:
    """
    Updates a single collection with the values passed.

    :param import_id str: The collection import_id to change.
    :param CollectionDTO collection: The DTO with all the values to change (or keep).
    :raises RepositoryError: raised on a database error.
    :raises ValidationError: raised should the import_id be invalid.
    :return Optional[CollectionDTO]: The updated collection or None if not updated.
    """

    # TODO: implement changing of a collection's organisation
    # org_id = organisation.get_id(db, collection.organisation)

    validate_import_id(import_id)
    try:
        with db_session.get_db() as db:
            if collection_repo.update(db, import_id, collection):
                db.commit()
                return get(import_id)
    except exc.SQLAlchemyError:
        _LOGGER.exception(f"When updating collection '{import_id}'")
        raise RepositoryError(f"Error when updating collection '{import_id}'")


@db_session.with_transaction(__name__)
@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def create(collection: CollectionCreateDTO, db: Session = db_session.get_db()) -> str:
    """
    Creates a new collection with the values passed.

    :param CollectionDTO collection: The values for the new collection.
    :raises RepositoryError: raised on a database error
    :raises ValidationError: raised should the import_id be invalid.
    :return str: The new import_id for the collection.
    """
    try:
        org_id = organisation.get_id(db, collection.organisation)

        return collection_repo.create(db, collection, org_id)

    except exc.SQLAlchemyError:
        _LOGGER.exception(f"When creating collection '{collection.description}'")
        raise RepositoryError(
            f"Error when creating collection '{collection.description}'"
        )


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


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def count() -> Optional[int]:
    """
    Gets a count of collections from the repository.

    :return Optional[int]: The number of collections in the repository or none.
    """
    try:
        with db_session.get_db() as db:
            return collection_repo.count(db)
    except exc.SQLAlchemyError as e:
        _LOGGER.error(e)
        raise RepositoryError(str(e))
