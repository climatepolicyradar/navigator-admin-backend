"""
Collection Service

This layer uses the collection repo to handle storage management and other
services for validation etc.
"""
import logging
from typing import Optional
from app.errors.repository_error import RepositoryError
from app.model.collection import CollectionDTO
import app.repository.collection as collection_repo
import app.db.session as db_session
from sqlalchemy import exc

from app.service import id


_LOGGER = logging.getLogger(__name__)


def get(import_id: str) -> Optional[CollectionDTO]:
    """
    Gets a collection given the import_id.

    :param str import_id: The import_id to use to get the collection.
    :raises RepositoryError: raised on a database error.
    :raises ValidationError: raised should the import_id be invalid.
    :return Optional[CollectionDTO]: The collection found or None.
    """
    id.validate(import_id)
    try:
        with db_session.get_db() as db:
            return collection_repo.get(db, import_id)
    except exc.SQLAlchemyError as e:
        _LOGGER.error(e)
        raise RepositoryError(str(e))


# def all() -> list[CollectionDTO]:
#     """
#     Gets the entire list of collections from the repository.

#     :return list[CollectionDTO]: The list of collections.
#     """
#     with db_session.get_db() as db:
#         return collection_repo.all(db)


# def search(search_term: str) -> list[CollectionDTO]:
#     """
#     Searches the title and descriptions of all the collections for the search term.

#     :param str search_term: Search pattern to match.
#     :return list[CollectionDTO]: The list of collections matching the search term.
#     """
#     with db_session.get_db() as db:
#         return collection_repo.search(db, search_term)


# @db_session.with_transaction(__name__)
# def update(collection: CollectionDTO, db: Session = db_session.get_db())
# -> Optional[CollectionDTO]:
#     """
#     Updates a single collection with the values passed.

#     :param CollectionDTO collection: The DTO with all the values to change (or keep).
#     :raises RepositoryError: raised on a database error.
#     :raises ValidationError: raised should the import_id be invalid.
#     :return Optional[CollectionDTO]: The updated collection or None if not updated.
#     """
#     id.validate(collection.import_id)
#     geo_id = geography.validate(db, collection.geography)
#     category.validate(collection.category)
#     org_id = organisation.validate(db, collection.organisation)
#     metadata.validate(db, org_id, collection.metadata)

#     if collection_repo.update(db, collection, geo_id):
#         db.commit()
#         return get(collection.import_id)


# @db_session.with_transaction(__name__)
# def create(collection: CollectionDTO, db: Session = db_session.get_db())
# -> Optional[CollectionDTO]:
#     """
#     Creates a new collection with the values passed.

#     :param CollectionDTO collection: The values for the new collection.
#     :raises RepositoryError: raised on a database error
#     :raises ValidationError: raised should the import_id be invalid.
#     :return Optional[CollectionDTO]: The new created collection or
# None if unsuccessful.
#     """
#     id.validate(collection.import_id)
#     geo_id = geography.validate(db, collection.geography)
#     category.validate(collection.category)
#     org_id = organisation.validate(db, collection.organisation)
#     metadata.validate(db, org_id, collection.metadata)

#     return collection_repo.create(db, collection, geo_id, org_id)


# @db_session.with_transaction(__name__)
# def delete(import_id: str, db: Session = db_session.get_db()) -> bool:
#     """
#     Deletes the collection specified by the import_id.

#     :param str import_id: The import_id of the collection to delete.
#     :raises RepositoryError: raised on a database error.
#     :raises ValidationError: raised should the import_id be invalid.
#     :return bool: True if deleted else False.
#     """
#     id.validate(import_id)
#     return collection_repo.delete(db, import_id)
