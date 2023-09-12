"""Operations on the repository for the Collection entity."""

import logging
from typing import Optional, Tuple, cast

from sqlalchemy.orm import Session
from app.db.models.app.users import Organisation
from app.db.models.law_policy.collection import CollectionFamily, CollectionOrganisation
from app.db.models.law_policy.family import Family, Slug
from app.errors import RepositoryError
from app.model.collection import CollectionDTO
from app.db.models.law_policy import Collection
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Query

from sqlalchemy import or_, update as db_update, delete as db_delete
from sqlalchemy_utils import escape_like

from app.repository.helpers import generate_slug

_LOGGER = logging.getLogger(__name__)

CollectionOrg = Tuple[Collection, Organisation]


def _collection_org_from_dto(
    dto: CollectionDTO, org_id: int
) -> Tuple[Collection, Organisation]:
    return (
        Collection(
            import_id=dto.import_id,
            title=dto.title,
            description=dto.description,
        ),
        CollectionOrganisation(
            collection_import_id=dto.import_id, organisation_id=org_id
        ),
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


def _collection_to_dto(db: Session, co: CollectionOrg) -> CollectionDTO:
    collection, org = co
    families = (
        db.query(Family.import_id)
        .join(CollectionFamily, CollectionFamily.family_import_id == Family.import_id)
        .filter(CollectionFamily.collection_import_id == collection.import_id)
        .all()
    )
    return CollectionDTO(
        import_id=str(collection.import_id),
        title=str(collection.title),
        description=str(collection.description),
        organisation=cast(str, org.name),
        families=[cast(str, f) for f in families],
    )


def all(db: Session) -> list[CollectionDTO]:
    """
    Returns all the collections.

    :return Optional[CollectionResponse]: All of things
    """
    collections = _get_query(db).all()

    if not collections:
        return []

    result = [_collection_to_dto(db, c) for c in collections]

    return result


def get(db: Session, import_id: str) -> Optional[CollectionDTO]:
    """
    Gets a single collection from the repository.

    :param str import_id: The import_id of the collection
    :return Optional[CollectionResponse]: A single collection or nothing
    """
    try:
        collection_org = _get_query(db).filter(Collection.import_id == import_id).one()
    except NoResultFound as e:
        _LOGGER.error(e)
        return

    return _collection_to_dto(db, collection_org)


def search(db: Session, search_term: str) -> list[CollectionDTO]:
    """
    Gets a list of collections from the repository searching title and summary.

    :param str search_term: Any search term to filter on title or summary
    :return Optional[list[CollectionResponse]]: A list of matches
    """
    term = f"%{escape_like(search_term)}%"
    search = or_(Collection.title.ilike(term), Collection.description.ilike(term))
    found = _get_query(db).filter(search).all()

    return [_collection_to_dto(db, f) for f in found]


def update(db: Session, collection: CollectionDTO) -> bool:
    """
    Updates a single entry with the new values passed.

    :param str import_id: The collection import id to change.
    :param CollectionDTO collection: The new values
    :return bool: True if new values were set otherwise false.
    """
    new_values = collection.dict()

    original_collection = (
        db.query(Collection)
        .filter(Collection.import_id == collection.import_id)
        .one_or_none()
    )

    if original_collection is None:  # Not found the collection to update
        _LOGGER.error(f"Unable to find collection for update {collection}")
        return False

    # We will need to update the slug if the title has changed
    update_title = cast(str, original_collection.title) != collection.title

    result = db.execute(
        db_update(Collection)
        .where(Collection.import_id == collection.import_id)
        .values(
            title=new_values["title"],
            description=new_values["summary"],
        )
    )
    if result.rowcount == 0:  # type: ignore
        msg = "Could not update collection fields: {collection}"
        _LOGGER.error(msg)
        raise RepositoryError(msg)

    # update slug if title changed
    if update_title:
        db.flush()
        name = generate_slug(db, collection.title)
        new_slug = Slug(
            collection_import_id=collection.import_id,
            collection_document_import_id=None,
            name=name,
        )
        db.add(new_slug)
        _LOGGER.info(f"Added a new slug for {collection.import_id} of {new_slug.name}")

    return True


def create(
    db: Session, collection: CollectionDTO, org_id: int
) -> Optional[CollectionDTO]:
    """
    Creates a new collection.

    :param CollectionDTO collection: the values for the new collection
    :param int org_id: a validated organisation id
    :return Optional[CollectionDTO]: the new collection created
    """
    try:
        new_collection, new_fam_org = _collection_org_from_dto(collection, org_id)
        db.add(new_collection)
        db.add(new_fam_org)
    except Exception as e:
        _LOGGER.error(e)
        return

    # Add a slug
    db.add(
        Slug(
            collection_import_id=collection.import_id,
            collection_document_import_id=None,
            name=generate_slug(db, collection.title),
        )
    )

    return collection


def delete(db: Session, import_id: str) -> bool:
    """
    Deletes a single collection by the import id.

    :param str import_id: The collection import id to delete.
    :return bool: True if deleted False if not.
    """
    command = db_delete(Collection).where(Collection.import_id == import_id)
    result = db.execute(command)

    return result.rowcount > 0  # type: ignore
