"""Operations on the repository for the Collection entity."""

import logging
import os
from datetime import datetime
from typing import Optional, Tuple, Union, cast

from db_client.models.dfce import Collection
from db_client.models.dfce.collection import CollectionFamily, CollectionOrganisation
from db_client.models.dfce.family import (
    Family,
    Slug,
)
from db_client.models.organisation.counters import CountedEntity
from db_client.models.organisation.users import Organisation
from sqlalchemy import Column, and_, desc, or_
from sqlalchemy import delete as db_delete
from sqlalchemy import update as db_update
from sqlalchemy.exc import NoResultFound, OperationalError
from sqlalchemy.orm import Query, Session
from sqlalchemy_utils import escape_like

from app.errors import RepositoryError
from app.model.collection import (
    CollectionCreateDTO,
    CollectionReadDTO,
    CollectionWriteDTO,
)
from app.model.general import Json
from app.repository.helpers import (
    generate_import_id,
    generate_slug,
)

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

CollectionOrg = Tuple[Collection, Organisation, Slug]


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
            import_id=dto.import_id if dto.import_id else None,
            title=dto.title,
            description=dto.description,
            valid_metadata=dto.metadata,
        ),
        CollectionOrganisation(collection_import_id="", organisation_id=org_id),
    )


def _get_query(db: Session) -> Query:
    # NOTE: SqlAlchemy will make a complete hash of the query generation
    #       if columns are used in the query() call. Therefore, entire
    #       objects are returned.
    return (
        db.query(Collection, Organisation, Slug)
        .join(
            CollectionOrganisation,
            CollectionOrganisation.collection_import_id == Collection.import_id,
        )
        .join(Organisation, Organisation.id == CollectionOrganisation.organisation_id)
        .outerjoin(Slug, Slug.collection_import_id == Collection.import_id)
    )


def _collection_to_dto(db: Session, co: CollectionOrg) -> CollectionReadDTO:
    collection, org, slug = co
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
        metadata=cast(Json, collection.valid_metadata),
        organisation=cast(str, org.name),
        families=families,
        created=cast(datetime, collection.created),
        last_modified=cast(datetime, collection.last_modified),
        slug=cast(str, slug.name) if slug else None,
    )


def validate(db: Session, import_ids: set[str]) -> bool:
    """Validate whether the given collection import IDs exist in the DB.

    :param Session db: The DB session to connect to.
    :param set[str] import_ids: The collection import IDs we want to
        check the existence of.
    :return bool: Return whether or not all the IDs exists in the DB.
    """
    matches_in_set = (
        db.query(Collection).filter(Collection.import_id.in_(import_ids)).count()
    )
    return bool(len(import_ids) == matches_in_set)


def all(db: Session, org_id: Optional[int]) -> list[CollectionReadDTO]:
    """
    Returns all the collections.

    :param db Session: the database connection
    :param org_id int: the ID of the organisation the user belongs to
    :return Optional[CollectionResponse]: All of things
    """
    query = _get_query(db)
    if org_id is not None:
        query = query.filter(Organisation.id == org_id)
    collections = query.order_by(desc(Collection.last_modified)).all()

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
        _LOGGER.debug(e)
        return

    return _collection_to_dto(db, collection_org)


def search(
    db: Session, search_params: dict[str, Union[str, int]], org_id: Optional[int]
) -> list[CollectionReadDTO]:
    """
    Gets a list of collections from the repo searching given fields.

    :param db Session: the database connection
    :param dict search_params: Any search terms to filter on specified
        fields (title & summary by default if 'q' specified).
    :param org_id Optional[int]: the ID of the organisation the user belongs to
    :raises HTTPException: If a DB error occurs a 503 is returned.
    :raises HTTPException: If the search request times out a 408 is
        returned.
    :return list[CollectionResponse]: A list of matching collections.
    """
    search = []
    if "q" in search_params.keys():
        term = f"%{escape_like(search_params['q'])}%"
        search.append(
            or_(Collection.title.ilike(term), Collection.description.ilike(term))
        )

    condition = and_(*search) if len(search) > 1 else search[0]
    try:
        query = _get_query(db).filter(condition)
        if org_id is not None:
            query = query.filter(Organisation.id == org_id)
        found = (
            query.order_by(desc(Collection.last_modified))
            .limit(search_params["max_results"])
            .all()
        )
    except OperationalError as e:
        if "canceling statement due to statement timeout" in str(e):
            raise TimeoutError
        raise RepositoryError(e)

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
            valid_metadata=new_values["metadata"],
        )
    )
    if result.rowcount == 0:  # type: ignore
        msg = f"Could not update collection fields: {collection}"
        _LOGGER.error(msg)
        raise RepositoryError(msg)

    slug = (
        db.query(Slug).filter(
            Slug.collection_import_id == import_id,
        )
    ).one_or_none()

    if original_collection.title != new_values["title"] or slug is None:
        # Update the slug
        slug_update = db.execute(
            db_update(Slug)
            .where(
                Slug.collection_import_id == import_id,
                Slug.family_import_id.is_(None),
                Slug.family_document_import_id.is_(None),
            )
            .values(name=generate_slug(db, new_values["title"]))
        )
        if slug_update.row_count == 0:  # type: ignore
            msg = f"Could not update slug for collection {collection}"
            _LOGGER.error(msg)
            raise RepositoryError(msg)

    return True


def create(db: Session, collection: CollectionCreateDTO, org_id: int) -> str:
    """
    Creates a new collection.

    :param db Session: the database connection
    :param CollectionDTO collection: the values for the new collection
    :param int org_id: a validated organisation id
    :raises RepositoryError: If a collection could not be created
    :return str: import id of new collection
    """
    try:
        new_collection, collection_organisation = _collection_org_from_dto(
            collection, org_id
        )

        if not new_collection.import_id:
            new_collection.import_id = cast(
                Column, generate_import_id(db, CountedEntity.Collection, org_id)
            )
        db.add(new_collection)

        collection_organisation.collection_import_id = new_collection.import_id
        db.add(collection_organisation)
    except Exception as e:
        _LOGGER.error(e)
        raise RepositoryError(
            f"Could not create the collection {collection.description}"
        )

    # Add a slug
    db.add(
        Slug(
            family_import_id=None,
            collection_import_id=new_collection.import_id,
            family_document_import_id=None,
            name=generate_slug(db, collection.title),
        )
    )
    db.flush()

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


def count(db: Session, org_id: Optional[int]) -> Optional[int]:
    """
    Counts the number of collections in the repository.

    :param db Session: the database connection
    :param org_id Optional[int]: the ID of the organisation the user belongs to
    :return Optional[int]: The number of collections in the repository or none.
    """
    try:
        query = _get_query(db)
        if org_id is not None:
            query = query.filter(Organisation.id == org_id)
        n_collections = query.count()
    except Exception as e:
        _LOGGER.error(e)
        return

    return n_collections
