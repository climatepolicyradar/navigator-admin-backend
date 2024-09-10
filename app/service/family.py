"""
Family Service

This file hands off to the family repo, adding the dependency of the db (future)
"""

import logging
from typing import Optional, Union

from pydantic import ConfigDict, validate_call
from sqlalchemy import exc
from sqlalchemy.orm import Session

import app.clients.db.session as db_session
from app.errors import AuthorisationError, RepositoryError, ValidationError
from app.model.family import FamilyCreateDTO, FamilyReadDTO, FamilyWriteDTO
from app.model.user import UserContext
from app.repository import family_repo
from app.service import (
    app_user,
    category,
    collection,
    corpus,
    geography,
    id,
    metadata,
    organisation,
)

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
def all(user: UserContext) -> list[FamilyReadDTO]:
    """
    Gets the entire list of families from the repository.

    :param UserContext user: The current user context.
    :return list[FamilyDTO]: The list of families.
    """
    with db_session.get_db() as db:
        org_id = app_user.restrict_entities_to_user_org(user)
        return family_repo.all(db, org_id)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def search(
    search_params: dict[str, Union[str, int]], user: UserContext
) -> list[FamilyReadDTO]:
    """
    Searches for the search term against families on specified fields.

    Where 'q' is used instead of an explicit field name, the titles and
    descriptions of all the Families are searched for the given term
    only.

    :param dict search_params: Search patterns to match against specified
        fields, given as key value pairs in a dictionary.
    :param UserContext user: The current user context.
    :return list[FamilyDTO]: The list of families matching the given
        search terms.
    """
    with db_session.get_db() as db:
        org_id = app_user.restrict_entities_to_user_org(user)
        return family_repo.search(db, search_params, org_id)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def validate_import_id(import_id: str) -> None:
    """
    Validates the import id for a family.

    :param str import_id: import id to check.
    :raises ValidationError: raised should the import_id be invalid.
    """
    id.validate(import_id)


@db_session.with_database()
@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def update(
    import_id: str,
    user: UserContext,
    family_dto: FamilyWriteDTO,
    db: Optional[Session] = None,
) -> Optional[FamilyReadDTO]:
    """
    Updates a single Family with the values passed.

    :param FamilyDTO family: The DTO with all the values to change (or keep).
    :raises RepositoryError: raised on a database error.
    :raises ValidationError: raised should the import_id be invalid.
    :return Optional[FamilyDTO]: The updated Family or None if not updated.
    """

    # Validate import_id
    validate_import_id(import_id)

    # Get family we're going to update
    family = get(import_id)
    if family is None:
        return None

    # Validate category
    category.validate(family_dto.category)

    if db is None:
        db = db_session.get_db()

    # Validate geography
    geo_id = geography.get_id(db, family_dto.geography)

    # Validate family belongs to same org as current user.
    entity_org_id: int = corpus.get_corpus_org_id(family.corpus_import_id, db)
    app_user.raise_if_unauthorised_to_make_changes(
        user, entity_org_id, family.corpus_import_id
    )

    # Validate metadata.
    metadata.validate_metadata(db, family.corpus_import_id, family_dto.metadata)

    # Validate that the collections we want to update are from the same organisation as
    # the current user and are in a valid format.
    all_cols_to_modify = set(family.collections).union(set(family_dto.collections))
    collection.validate_multiple_ids(all_cols_to_modify)
    collection.validate(all_cols_to_modify, db)

    collections_not_in_user_org = [
        collection.get_org_from_id(db, c) != entity_org_id for c in all_cols_to_modify
    ]
    if len(collections_not_in_user_org) > 0 and any(collections_not_in_user_org):
        msg = "Organisation mismatch between some collections and the current user"
        _LOGGER.error(msg)
        raise ValidationError(msg)

    try:
        if family_repo.update(db, import_id, family_dto, geo_id):
            db.commit()
        else:
            db.rollback()
    except Exception as e:
        db.rollback()
        raise e
    return get(import_id)


@db_session.with_database()
@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def create(
    family: FamilyCreateDTO,
    user: UserContext,
    db: Optional[Session] = None,
) -> str:
    """
    Creates a new Family with the values passed.

    :param FamilyDTO family: The values for the new Family.
    :param UserContext user: The current user context.
    :raises RepositoryError: raised on a database error
    :raises ValidationError: raised should the import_id be invalid.
    :return Optional[FamilyDTO]: The new created Family or None if unsuccessful.
    """

    if db is None:
        db = db_session.get_db()

    # Validate geographies
    geo_ids = []
    if isinstance(family.geographies, str):
        geo_ids.append(geography.get_id(db, family.geographies))
    elif isinstance(family.geographies, list):
        for geo_id in family.geographies:
            geo_ids.append(geography.get_id(db, geo_id))

    # Validate category
    category.validate(family.category)

    # Get the organisation from the user's email
    corpus.validate(db, family.corpus_import_id)
    entity_org_id: int = corpus.get_corpus_org_id(family.corpus_import_id, db)

    # Validate collection ids.
    collections = set(family.collections)
    collection.validate_multiple_ids(collections)
    collection.validate(collections, db)

    # Validate that the collections we want to update are from the same organisation as
    # the current user.
    collections_not_in_user_org = [
        collection.get_org_from_id(db, c) != entity_org_id for c in collections
    ]
    if len(collections_not_in_user_org) > 0 and any(collections_not_in_user_org):
        msg = "Organisation mismatch between some collections and the current user"
        _LOGGER.error(msg)
        raise AuthorisationError(msg)

    # Validate that the corpus we want to add the new family to exists and is from the
    # same organisation as the user.
    app_user.raise_if_unauthorised_to_make_changes(
        user, entity_org_id, family.corpus_import_id
    )

    # Validate metadata.
    metadata.validate_metadata(db, family.corpus_import_id, family.metadata)

    try:
        import_id = family_repo.create(db, family, geo_ids, entity_org_id)
        if len(import_id) == 0:
            db.rollback()
        return import_id
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.commit()


@db_session.with_database()
@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def delete(
    import_id: str, user: UserContext, db: Optional[Session] = None
) -> Optional[bool]:
    """
    Deletes the Family specified by the import_id.

    :param str import_id: The import_id of the Family to delete.
    :param UserContext user: The current user context.
    :raises RepositoryError: raised on a database error.
    :raises ValidationError: raised should the import_id be invalid.
    :return bool: True if deleted else False.
    """
    id.validate(import_id)

    # Get family we're going to delete.
    family = get(import_id)
    if family is None:
        return None

    if db is None:
        db = db_session.get_db()

    # Validate family belongs to same org as current user.
    entity_org_id = organisation.get_id_from_name(db, family.organisation)
    app_user.raise_if_unauthorised_to_make_changes(user, entity_org_id, import_id)
    try:
        if result := family_repo.delete(db, import_id):
            db.commit()
        else:
            db.rollback()
        return result
    except Exception as e:
        db.rollback()
        raise e
