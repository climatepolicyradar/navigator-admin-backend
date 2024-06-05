import logging
from typing import Optional, Tuple, Union

from pydantic import ConfigDict, validate_call
from sqlalchemy import exc
from sqlalchemy.orm import Session

import app.clients.db.session as db_session
import app.repository.document as document_repo
import app.repository.document_file as file_repo
import app.service.family as family_service
from app.clients.aws.client import get_s3_client
from app.errors import RepositoryError, ValidationError
from app.model.document import DocumentCreateDTO, DocumentReadDTO, DocumentWriteDTO
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
def all(user_email: str) -> list[DocumentReadDTO]:
    """
    Gets the entire list of documents from the repository.

    :param str user_email: The email address of the current user.
    :return list[documentDTO]: The list of documents.
    """
    with db_session.get_db() as db:
        org_id = app_user.restrict_entities_to_user_org(db, user_email)
        return document_repo.all(db, org_id)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def search(
    query_params: dict[str, Union[str, int]], user_email: str
) -> list[DocumentReadDTO]:
    """
    Searches for the search term against documents on specified fields.

    Where 'q' is used instead of an explicit field name, only the titles
    of all the documents are searched for the given term.

    :param dict query_params: Search patterns to match against specified
        fields, given as key value pairs in a dictionary.
    :param str user_email: The email address of the current user.
    :return list[DocumentReadDTO]: The list of documents matching the
        given search terms.
    """
    with db_session.get_db() as db:
        org_id = app_user.restrict_entities_to_user_org(db, user_email)
        return document_repo.search(db, query_params, org_id)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def validate_import_id(import_id: str) -> None:
    """
    Validates the import id for a document.

    :param str import_id: import id to check.
    :raises ValidationError: raised should the import_id be invalid.
    """
    id.validate(import_id)


@db_session.with_transaction(__name__)
@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def update(
    import_id: str,
    document: DocumentWriteDTO,
    context=None,
    db: Session = db_session.get_db(),
) -> Optional[DocumentReadDTO]:
    """
    Updates a single document with the values passed.

    :param documentDTO document: The DTO with all the values to change (or keep).
    :raises RepositoryError: raised on a database error.
    :raises ValidationError: raised should the import_id be invalid.
    :return Optional[documentDTO]: The updated document or None if not updated.
    """
    validate_import_id(import_id)
    if context is not None:
        context.error = f"Error when updating document {import_id}"

    if document.variant_name == "":
        raise ValidationError("Variant name is empty")

    document_repo.update(db, import_id, document)
    db.commit()
    return get(import_id)


@db_session.with_transaction(__name__)
@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def create(
    document: DocumentCreateDTO,
    user_email: str,
    context=None,
    db: Session = db_session.get_db(),
) -> str:
    """
        Creates a new document with the values passed.

        :param documentDTO document: The values for the new document.
        :raises RepositoryError: raised on a database error
        :raises ValidationError: raised should the import_id be invalid.
        :return Optional[documentDTO]: The new created document or
    None if unsuccessful.
    """
    id.validate(document.family_import_id)
    if context is not None:
        context.error = (
            f"Could not create document for family {document.family_import_id}"
        )

    if document.variant_name == "":
        raise ValidationError("Variant name is empty")

    family = family_service.get(document.family_import_id)
    if family is None:
        raise ValidationError(f"Could not find family for {document.family_import_id}")

    entity_org_id = get_org_from_id(db, family.import_id)
    app_user.is_authorised_to_make_changes(
        db, user_email, entity_org_id, family.import_id
    )
    return document_repo.create(db, document)


@db_session.with_transaction(__name__)
@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def delete(
    import_id: str, user_email: str, context=None, db: Session = db_session.get_db()
) -> Optional[bool]:
    """
    Deletes the document specified by the import_id.

    :param str import_id: The import_id of the document to delete.
    :param str user_email: The email address of the current user.
    :raises RepositoryError: raised on a database error.
    :raises ValidationError: raised should the import_id be invalid.
    :return bool: True if deleted None if not.
    """
    id.validate(import_id)

    if context is not None:
        context.error = f"Could not delete document {import_id}"

    doc = get(import_id)
    if doc is None:
        return None

    entity_org_id = get_org_from_id(db, import_id)
    app_user.is_authorised_to_make_changes(db, user_email, entity_org_id, import_id)
    return document_repo.delete(db, import_id)


def get_org_from_id(db: Session, import_id: str) -> int:
    org = document_repo.get_org_from_import_id(db, import_id)
    if org is None:
        msg = f"The document import id {import_id} does not have an associated organisation"
        _LOGGER.error(msg)
        raise ValidationError(msg)
    return org
