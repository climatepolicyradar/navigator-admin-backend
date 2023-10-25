"""Operations on the repository for the Collection entity."""

import logging
from typing import Optional, Tuple, cast

from sqlalchemy.orm import Session
from sqlalchemy import Column
from app.clients.db.models.app.counters import CountedEntity
from app.clients.db.models.app.users import Organisation
from app.clients.db.models.law_policy.collection import (
    CollectionFamily,
    CollectionOrganisation,
)
from app.clients.db.models.law_policy.family import Family
from app.errors import RepositoryError
from app.model.collection import (
    CollectionCreateDTO,
    CollectionReadDTO,
    CollectionWriteDTO,
)
from app.clients.db.models.law_policy import Collection
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Query

from sqlalchemy import or_, update as db_update, delete as db_delete
from sqlalchemy_utils import escape_like

from app.repository.helpers import generate_import_id


_LOGGER = logging.getLogger(__name__)

CollectionOrg = Tuple[Collection, Organisation]


def get_org_from_collection_id(db: Session, collection_import_id: str) -> Optional[int]:
    return (
        db.query(CollectionOrganisation.organisation_id)
        .filter_by(collection_import_id=collection_import_id)
        .scalar()
    )


def _collection_org_from_dto(
    dto: CollectionCreateDTO, org_id: int
) -> Tuple[Collection, CollectionOrganisation]:
    return (
        Collection(
            import_id="",
            title=dto.title,
            description=dto.description,
        ),
        CollectionOrganisation(collection_import_id="", organisation_id=org_id),
    )


def _get_query(db: Session) -> Query:
    # NOTE: SqlAlchemy will make a complete hash of the query generation
    #       if columns are used in the query() call. Therefore, entire
    #       objects are returned.
    return (
        db.query(Collection, Organisation)
        .join(
            CollectionOrganisation,
            CollectionOrganisation.collection_import_id == Collection.import_id,
        )
        .join(Organisation, Organisation.id == CollectionOrganisation.organisation_id)
    )


def _collection_to_dto(db: Session, co: CollectionOrg) -> CollectionReadDTO:
    collection, org = co
    db_families = (
        db.query(Family.import_id)
        .join(CollectionFamily, CollectionFamily.family_import_id == Family.import_id)
        .filter(CollectionFamily.collection_import_id == collection.import_id)
        .all()
    )
    families = [cast(str, f[0]) for f in db_families]
    return CollectionReadDTO(
        import_id=str(collection.import_id),
        title=str(collection.title),
        description=str(collection.description),
        organisation=cast(str, org.name),
        families=families,
    )


def all(db: Session) -> list[CollectionReadDTO]:
    """
    Returns all the collections.

    :param db Session: the database connection
    :return Optional[CollectionResponse]: All of things
    """
    collections = _get_query(db).all()

    if not collections:
        return []

    result = [_collection_to_dto(db, c) for c in collections]

    return result


def get(db: Session, import_id: str) -> Optional[CollectionReadDTO]:
    """
    Gets a single collection from the repository.

    :param db Session: the database connection
    :param str import_id: The import_id of the collection
    :return Optional[CollectionResponse]: A single collection or nothing
    """
    try:
        collection_org = _get_query(db).filter(Collection.import_id == import_id).one()
    except NoResultFound as e:
        _LOGGER.error(e)
        return

    return _collection_to_dto(db, collection_org)


def search(db: Session, search_term: str) -> list[CollectionReadDTO]:
    """
    Gets a list of collections from the repository searching title and summary.

    :param db Session: the database connection
    :param str search_term: Any search term to filter on title or summary
    :return Optional[list[CollectionResponse]]: A list of matches
    """
    term = f"%{escape_like(search_term)}%"
    search = or_(Collection.title.ilike(term), Collection.description.ilike(term))
    found = _get_query(db).filter(search).all()

    return [_collection_to_dto(db, f) for f in found]


def update(db: Session, import_id: str, collection: CollectionWriteDTO) -> bool:
    """
    Updates a single entry with the new values passed.

    :param db Session: the database connection
    :param str import_id: The collection import id to change.
    :param CollectionDTO collection: The new values
    :return bool: True if new values were set otherwise false.
    """
    new_values = collection.model_dump()

    original_collection = (
        db.query(Collection).filter(Collection.import_id == import_id).one_or_none()
    )

    if original_collection is None:  # Not found the collection to update
        _LOGGER.error(f"Unable to find collection for update {collection}")
        return False

    result = db.execute(
        db_update(Collection)
        .where(Collection.import_id == import_id)
        .values(
            title=new_values["title"],
            description=new_values["description"],
        )
    )
    if result.rowcount == 0:  # type: ignore
        msg = f"Could not update collection fields: {collection}"
        _LOGGER.error(msg)
        raise RepositoryError(msg)

    return True


def create(db: Session, collection: CollectionCreateDTO, org_id: int) -> str:
    """
    Creates a new collection.

    :param db Session: the database connection
    :param CollectionDTO collection: the values for the new collection
    :param int org_id: a validated organisation id
    :return bool: True if new collection was created otherwise false.
    """
    try:
        new_collection, collection_organisation = _collection_org_from_dto(
            collection, org_id
        )
        new_collection.import_id = cast(
            Column, generate_import_id(db, CountedEntity.Collection, org_id)
        )
        db.add(new_collection)

        collection_organisation.collection_import_id = new_collection.import_id
        db.add(collection_organisation)
        db.flush()
    except Exception as e:
        _LOGGER.error(e)
        raise RepositoryError(
            f"Could not create the collection {collection.description}"
        )

    return cast(str, new_collection.import_id)


def delete(db: Session, import_id: str) -> bool:
    """
    Deletes a single collection by the import id.

    :param db Session: the database connection
    :param str import_id: The collection import id to delete.
    :return bool: True if deleted False if not.
    """
    commands = [
        db_delete(CollectionOrganisation).where(
            CollectionOrganisation.collection_import_id == import_id
        ),
        db_delete(CollectionFamily).where(
            CollectionFamily.collection_import_id == import_id
        ),
        db_delete(Collection).where(Collection.import_id == import_id),
    ]
    for c in commands:
        result = db.execute(c)

    return result.rowcount > 0  # type: ignore


def count(db: Session) -> Optional[int]:
    """
    Counts the number of collections in the repository.

    :param db Session: the database connection
    :return Optional[int]: The number of collections in the repository or none.
    """
    try:
        n_collections = _get_query(db).count()
    except Exception as e:
        _LOGGER.error(e)
        return

    return n_collections
