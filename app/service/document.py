import logging
from typing import Optional, Tuple, Union, cast

from pydantic import ConfigDict, validate_call
from sqlalchemy import exc
from sqlalchemy.orm import Session

import app.clients.db.session as db_session
import app.repository.document as document_repo
import app.repository.document_file as file_repo
import app.repository.family as family_repo
import app.service.family as family_service
from app.clients.aws.client import get_s3_client
from app.errors import RepositoryError, ValidationError
from app.model.document import DocumentCreateDTO, DocumentReadDTO, DocumentWriteDTO
from app.model.user import UserContext
from app.service import app_user, id

_LOGGER = logging.getLogger(__name__)


def get_upload_details(filename: str, overwrite: Optional[bool]) -> Tuple[str, str]:
    client = get_s3_client()

    # TODO : Check if file pre-exists so we can use "overwrite"
    return file_repo.get_upload_details(client, filename)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def get(import_id: str) -> Optional[DocumentReadDTO]:
    """
    Gets a document given the import_id.

    :param str import_id: The import_id to use to get the document.
    :raises RepositoryError: raised on a database error.
    :raises ValidationError: raised should the import_id be invalid.
    :return Optional[documentDTO]: The document found or None.
    """
    validate_import_id(import_id)
    try:
        with db_session.get_db() as db:
            return document_repo.get(db, import_id)
    except exc.SQLAlchemyError as e:
        _LOGGER.error(e)
        raise RepositoryError(str(e))


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def all(user: UserContext) -> list[DocumentReadDTO]:
    """
    Gets the entire list of documents from the repository.

    :param UserContext user: The current user context.
    :return list[documentDTO]: The list of documents.
    """
    with db_session.get_db() as db:
        org_id = app_user.restrict_entities_to_user_org(user)
        return document_repo.all(db, org_id)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def search(
    query_params: dict[str, Union[str, int]], user: UserContext
) -> list[DocumentReadDTO]:
    """
    Searches for the search term against documents on specified fields.

    Where 'q' is used instead of an explicit field name, only the titles
    of all the documents are searched for the given term.

    :param dict query_params: Search patterns to match against specified
        fields, given as key value pairs in a dictionary.
    :param UserContext user: The current user context.
    :return list[DocumentReadDTO]: The list of documents matching the
        given search terms.
    """
    with db_session.get_db() as db:
        org_id = app_user.restrict_entities_to_user_org(user)
        return document_repo.search(db, query_params, org_id)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def validate_import_id(import_id: str) -> None:
    """
    Validates the import id for a document.

    :param str import_id: import id to check.
    :raises ValidationError: raised should the import_id be invalid.
    """
    id.validate(import_id)


@db_session.with_database()
@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def update(
    import_id: str,
    document: DocumentWriteDTO,
    user: UserContext,
    db: Optional[Session],
) -> Optional[DocumentReadDTO]:
    """
    Updates a single document with the values passed.

    :param str import_id: The import ID of the document to update.
    :param documentDTO document: The DTO with all the values to change (or keep).
    :param UserContext user: The current user context.
    :raises AuthorisationError: raised if user has incorrect permissions.
    :raises RepositoryError: raised on a database error.
    :raises ValidationError: raised should the import_id be invalid.
    :return Optional[documentDTO]: The updated document or None if not updated.
    """
    validate_import_id(import_id)

    if db is None:
        db = db_session.get_db()

    doc = get(import_id)
    if doc is None:
        return None

    if document.variant_name == "":
        raise ValidationError("Variant name is empty")

    entity_org_id = get_org_from_id(db, import_id)
    app_user.raise_if_unauthorised_to_make_changes(user, entity_org_id, import_id)

    try:
        if document_repo.update(db, import_id, document):
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
    document: DocumentCreateDTO,
    user: UserContext,
    db: Optional[Session],
) -> str:
    """
    Creates a new document with the values passed.

    :param documentDTO document: The values for the new document.
    :param UserContext user: The current user context.
    :raises RepositoryError: raised on a database error
    :raises ValidationError: raised should the import_id be invalid.
    :return Optional[documentDTO]: The new created document or
    None if unsuccessful.
    """
    id.validate(document.family_import_id)

    if db is None:
        db = db_session.get_db()

    if document.variant_name == "":
        raise ValidationError("Variant name is empty")

    family = family_service.get(document.family_import_id)
    if family is None:
        raise ValidationError(f"Could not find family for {document.family_import_id}")

    entity_org_id = get_org_from_id(db, family.import_id, is_create=True)
    app_user.raise_if_unauthorised_to_make_changes(
        user, entity_org_id, family.import_id
    )

    try:
        import_id = document_repo.create(db, document)
        if len(import_id) == 0:
            db.rollback()
        else:
            db.commit()
        return import_id
    except Exception as e:
        db.rollback()
        raise e


@db_session.with_database()
@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def delete(import_id: str, user: UserContext, db: Optional[Session]) -> Optional[bool]:
    """
    Deletes the document specified by the import_id.

    :param str import_id: The import_id of the document to delete.
    :param UserContext user: The current user context.
    :raises RepositoryError: raised on a database error.
    :raises ValidationError: raised should the import_id be invalid.
    :return bool: True if deleted None if not.
    """
    id.validate(import_id)

    if db is None:
        db = db_session.get_db()

    doc = get(import_id)
    if doc is None:
        return None

    entity_org_id = get_org_from_id(db, import_id)
    app_user.raise_if_unauthorised_to_make_changes(user, entity_org_id, import_id)

    try:
        if result := document_repo.delete(db, import_id):
            db.commit()
        else:
            db.rollback()

        return result
    except Exception as e:
        db.rollback()
        raise e


def get_org_from_id(db: Session, import_id: str, is_create: bool = False) -> int:
    if not is_create:
        org = document_repo.get_org_from_import_id(db, import_id)
    else:
        org = family_repo.get_organisation(db, import_id)

    if org is None:
        msg = f"No organisation associated with import id {import_id}"
        _LOGGER.error(msg)
        raise ValidationError(msg)

    return org if isinstance(org, int) else cast(int, org.id)
