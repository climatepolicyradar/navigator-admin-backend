"""Operations on the repository for the Collection entity."""

import logging
from typing import Optional, Tuple, cast

from sqlalchemy.orm import Session
from app.db.models.app.users import Organisation
from app.db.models.law_policy.collection import CollectionFamily, CollectionOrganisation
from app.db.models.law_policy.family import Family
from app.model.collection import CollectionDTO
from app.db.models.law_policy import Collection
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Query


_LOGGER = logging.getLogger(__name__)

CollectionOrg = Tuple[Collection, Organisation]

# __        _____ ____
# \ \      / /_ _|  _ \
#  \ \ /\ / / | || |_) |
#   \ V  V /  | ||  __/
#    \_/\_/  |___|_|

# def _collection_org_from_dto(
#     dto: CollectionDTO, geo_id: int, org_id
# ) -> Tuple[Collection, Organisation]:
#     return (
#         Collection(
#             import_id=dto.import_id,
#             title=dto.title,
#             description=dto.summary,
#             geography_id=geo_id,
#             collection_category=dto.category,
#         ),
#         CollectionOrganisation(collection_import_id=dto.import_id,
#   organisation_id=org_id),
#     )


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


# def _generate_slug(
#     title: str,
#     lookup: set[str],
#     attempts: int = 100,
#     suffix_length: int = 4,
# ):
#     base = slugify(str(title))
#     # TODO: try to extend suffix length if attempts are exhausted
#     suffix = str(uuid4())[:suffix_length]
#     count = 0
#     while (slug := f"{base}_{suffix}") in lookup:
#         count += 1
#         suffix = str(uuid4())[:suffix_length]
#         if count > attempts:
#             raise RuntimeError(
#                 f"Failed to generate a slug for {base} after {attempts} attempts."
#             )
#     lookup.add(slug)
#     return slug


# def _update_intention(db, collection, geo_id, original_collection):
#     update_title = cast(str, original_collection.title) != collection.title
#     update_basics = (
#         update_title
#         or original_collection.description != collection.summary
#         or original_collection.geography_id != geo_id
#         or original_collection.collection_category != collection.category
#     )
#     existing_metadata = (
#         db.query(CollectionMetadata)
#         .filter(CollectionMetadata.collection_import_id == collection.import_id)
#         .one()
#     )
#     update_metadata = existing_metadata.value != collection.metadata
#     return update_title, update_basics, update_metadata


def _collection_query(db: Session) -> Query:
    return (
        db.query(Collection, Organisation)
        .join(
            CollectionOrganisation,
            CollectionOrganisation.collection_import_id == Collection.import_id,
        )
        .join(Organisation, Organisation.id == CollectionOrganisation.organisation_id)
    )


def all(db: Session) -> list[CollectionDTO]:
    """
    Returns all the collections.

    :return Optional[CollectionResponse]: All of things
    """
    collections = _collection_query(db).all()

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
        collection_org = (
            _collection_query(db).filter(Collection.import_id == import_id).one()
        )
    except NoResultFound as e:
        _LOGGER.error(e)
        return

    return _collection_to_dto(db, collection_org)


# def search(db: Session, search_term: str) -> list[CollectionDTO]:
#     """
#     Gets a list of collections from the repository searching title and summary.

#     :param str search_term: Any search term to filter on title or summary
#     :return Optional[list[CollectionResponse]]: A list of matches
#     """
#     term = f"%{escape_like(search_term)}%"
#     search = or_(Collection.title.ilike(term), Collection.description.ilike(term))
#     found = _fam_geo_meta_query(db).filter(search).all()

#     return [_collection_to_dto(db, f) for f in found]


# def update(db: Session, collection: CollectionDTO, geo_id: int) -> bool:
#     """
#     Updates a single entry with the new values passed.

#     :param str import_id: The collection import id to change.
#     :param CollectionDTO collection: The new values
#     :param int geo_id: a validated geography id
#     :return Optional[CollectionDTO]: The new values set or None if not found.
#     """
#     new_values = collection.dict()

#     original_collection = (
#         db.query(Collection).filter(Collection.import_id == collection.import_id)
# .one_or_none()
#     )

#     if original_collection is None:  # Not found the collection to update
#         _LOGGER.error(f"Unable to find collection for update {collection}")
#         return False

#     # Now figure out the intention of the request:
#     update_title, update_basics, update_metadata = _update_intention(
#         db, collection, geo_id, original_collection
#     )

#     # Return if nothing to do
#     if not update_title and not update_basics and not update_metadata:
#         return True

#     # Update basic fields
#     if update_basics:
#         result = db.execute(
#             db_update(Collection)
#             .where(Collection.import_id == collection.import_id)
#             .values(
#                 title=new_values["title"],
#                 description=new_values["summary"],
#                 geography_id=geo_id,
#                 collection_category=new_values["category"],
#             )
#         )
#         if result.rowcount == 0:  # type: ignore
#             msg = "Could not update collection fields: {collection}"
#             _LOGGER.error(msg)
#             raise RepositoryError(msg)

#     # Update if metadata is changed
#     if update_metadata:
#         md_result = db.execute(
#             db_update(CollectionMetadata)
#             .where(CollectionMetadata.collection_import_id == collection.import_id)
#             .values(value=collection.metadata)
#         )
#         if md_result.rowcount == 0:  # type: ignore
#             msg = (
#                 "Could not update the metadata for collection: "
#                 + f"{collection.import_id} to {collection.metadata}"
#             )
#             _LOGGER.error(msg)
#             raise RepositoryError(msg)

#     # update slug if title changed
#     if update_title:
#         db.flush()
#         lookup = set([cast(str, n) for n in db.query(Slug.name).all()])
#         name = _generate_slug(collection.title, lookup)
#         new_slug = Slug(
#             collection_import_id=collection.import_id,
#             collection_document_import_id=None,
#             name=name,
#         )
#         db.add(new_slug)
#         _LOGGER.info(f"Added a new slug for {collection.import_id}
# of {new_slug.name}")

#     return True


# def create(
#     db: Session, collection: CollectionDTO, geo_id: int, org_id: int
# ) -> Optional[CollectionDTO]:
#     """
#     Creates a new collection.

#     :param CollectionDTO collection: the values for the new collection
#     :param int geo_id: a validated geography id
#     :return Optional[CollectionDTO]: the new collection created
#     """
#     try:
#         new_collection, new_fam_org = _collection_org_from_dto(collection,
# geo_id, org_id)
#         db.add(new_collection)
#         db.add(new_fam_org)
#     except Exception as e:
#         _LOGGER.error(e)
#         return

#     # Add a slug
#     lookup = set([cast(str, n) for n in db.query(Slug.name).all()])
#     db.add(
#         Slug(
#             collection_import_id=collection.import_id,
#             collection_document_import_id=None,
#             name=_generate_slug(collection.title, lookup),
#         )
#     )

#     # TODO: Validate the metadata

#     # Add the metadata
#     db.flush()
#     tax = (
#         db.query(MetadataOrganisation)
#         .filter(MetadataOrganisation.organisation_id == org_id)
#         .one()
#     )
#     db.add(
#         CollectionMetadata(
#             collection_import_id=new_collection.import_id,
#             taxonomy_id=tax.taxonomy_id,
#             value=collection.metadata,
#         )
#     )
#     return collection


# def delete(db: Session, import_id: str) -> bool:
#     """
#     Deletes a single collection by the import id.

#     :param str import_id: The collection import id to delete.
#     :return bool: True if deleted False if not.
#     """
#     commands = [
#         db_delete(CollectionOrganisation).where(
#             CollectionOrganisation.collection_import_id == import_id
#         ),
#         db_delete(CollectionMetadata).where(CollectionMetadata.
# collection_import_id == import_id),
#         db_delete(Collection).where(Collection.import_id == import_id),
#     ]
#     for c in commands:
#         result = db.execute(c)

#     return result.rowcount > 0  # type: ignore
