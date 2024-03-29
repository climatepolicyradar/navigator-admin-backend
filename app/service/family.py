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
from app.errors import RepositoryError, ValidationError
from app.model.family import FamilyCreateDTO, FamilyReadDTO, FamilyWriteDTO
from app.repository import family_repo
from app.service import (
    app_user,
    category,
    collection,
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
def all() -> list[FamilyReadDTO]:
    """
    Gets the entire list of families from the repository.

    :return list[FamilyDTO]: The list of families.
    """
    with db_session.get_db() as db:
        return family_repo.all(db)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def search(query_params: dict[str, Union[str, int]]) -> list[FamilyReadDTO]:
    """
    Searches for the search term against families on specified fields.

    Where 'q' is used instead of an explicit field name, the titles and
    descriptions of all the Families are searched for the given term
    only.

    :param dict query_params: Search patterns to match against specified
        fields, given as key value pairs in a dictionary.
    :return list[FamilyDTO]: The list of families matching the given
        search terms.
    """
    with db_session.get_db() as db:
        return family_repo.search(db, query_params)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def validate_import_id(import_id: str) -> None:
    """
    Validates the import id for a family.

    :param str import_id: import id to check.
    :raises ValidationError: raised should the import_id be invalid.
    """
    id.validate(import_id)


@db_session.with_transaction(__name__)
@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def update(
    import_id: str,
    user_email: str,
    family_dto: FamilyWriteDTO,
    db: Session = db_session.get_db(),
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

    # Validate category
    category.validate(family_dto.category)

    # Validate geography
    geo_id = geography.get_id(db, family_dto.geography)

    # Get family we're going to update
    family = get(import_id)
    if family is None:
        raise ValidationError(f"Could not find family {import_id}")

    # Validate family belongs to same org as current user.
    user_org_id = app_user.get_organisation(db, user_email)
    org_id = organisation.get_id(db, family.organisation)
    if org_id != user_org_id:
        msg = "Current user does not belong to the organisation that owns family "
        msg += import_id
        raise ValidationError(msg)

    # Validate metadata.
    metadata.validate(db, org_id, family_dto.metadata)

    # Validate that the collections we want to update are from the same organisation as
    # the current user and are in a valid format.
    all_cols_to_modify = set(family.collections).union(set(family_dto.collections))

    id.validate_multiple_ids(all_cols_to_modify)

    collections_not_in_user_org = [
        collection.get_org_from_id(db, c) != org_id for c in all_cols_to_modify
    ]
    if len(collections_not_in_user_org) > 0 and any(collections_not_in_user_org):
        msg = "Organisation mismatch between some collections and the current user"
        _LOGGER.error(msg)
        raise ValidationError(msg)

    if family_repo.update(db, import_id, family_dto, geo_id):
        db.commit()
        return get(import_id)


@db_session.with_transaction(__name__)
@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def create(
    family: FamilyCreateDTO, user_email: str, db: Session = db_session.get_db()
) -> str:
    """
    Creates a new Family with the values passed.

    :param FamilyDTO family: The values for the new Family.
    :raises RepositoryError: raised on a database error
    :raises ValidationError: raised should the import_id be invalid.
    :return Optional[FamilyDTO]: The new created Family or None if unsuccessful.
    """

    # Get the organisation from the user's email
    org_id = app_user.get_organisation(db, user_email)

    # Validate geography
    geo_id = geography.get_id(db, family.geography)

    # Validate category
    category.validate(family.category)

    # Validate metadata.
    metadata.validate(db, org_id, family.metadata)

    # Validate collection ids.
    collections = set(family.collections)
    id.validate_multiple_ids(collections)

    # Validate that the collections we want to update are from the same organisation as
    # the current user.
    collections_not_in_user_org = [
        collection.get_org_from_id(db, c) != org_id for c in collections
    ]
    if len(collections_not_in_user_org) > 0 and any(collections_not_in_user_org):
        msg = "Organisation mismatch between some collections and the current user"
        _LOGGER.error(msg)
        raise ValidationError(msg)

    return family_repo.create(db, family, geo_id, org_id)


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
    try:
        return family_repo.delete(db, import_id)
    except exc.SQLAlchemyError:
        msg = f"Unable to delete family {import_id}"
        _LOGGER.exception(msg)
        raise RepositoryError(msg)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def count() -> Optional[int]:
    """
    Gets a count of families from the repository.

    :return Optional[int]: The number of families in the repository or none.
    """
    try:
        with db_session.get_db() as db:
            return family_repo.count(db)
    except exc.SQLAlchemyError as e:
        _LOGGER.error(e)
        raise RepositoryError(str(e))
