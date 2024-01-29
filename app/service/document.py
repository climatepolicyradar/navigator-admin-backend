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
from app.clients.db.errors import RepositoryError, ValidationError
from app.model.document import DocumentCreateDTO, DocumentReadDTO, DocumentWriteDTO
from app.service import id

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
def all() -> list[DocumentReadDTO]:
    """
    Gets the entire list of documents from the repository.

    :return list[documentDTO]: The list of documents.
    """
    with db_session.get_db() as db:
        return document_repo.all(db)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def search(query_params: dict[str, Union[str, int]]) -> list[DocumentReadDTO]:
    """
    Searches for the search term against documents on specified fields.

    Where 'q' is used instead of an explicit field name, only the titles
    of all the documents are searched for the given term.

    :param dict query_params: Search patterns to match against specified
        fields, given as key value pairs in a dictionary.
    :return list[DocumentReadDTO]: The list of documents matching the
        given search terms.
    """
    with db_session.get_db() as db:
        return document_repo.search(db, query_params)


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
    import_id: str, document: DocumentWriteDTO, db: Session = db_session.get_db()
) -> Optional[DocumentReadDTO]:
    """
    Updates a single document with the values passed.

    :param documentDTO document: The DTO with all the values to change (or keep).
    :raises RepositoryError: raised on a database error.
    :raises ValidationError: raised should the import_id be invalid.
    :return Optional[documentDTO]: The updated document or None if not updated.
    """
    validate_import_id(import_id)

    if document.variant_name == "":
        raise ValidationError("Variant name is empty")

    try:
        if document_repo.update(db, import_id, document):
            db.commit()
            return get(import_id)

    except exc.SQLAlchemyError:
        _LOGGER.exception(f"While updating document {import_id}")
        raise RepositoryError(f"Error when updating document {import_id}")


@db_session.with_transaction(__name__)
@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def create(document: DocumentCreateDTO, db: Session = db_session.get_db()) -> str:
    """
        Creates a new document with the values passed.

        :param documentDTO document: The values for the new document.
        :raises RepositoryError: raised on a database error
        :raises ValidationError: raised should the import_id be invalid.
        :return Optional[documentDTO]: The new created document or
    None if unsuccessful.
    """
    id.validate(document.family_import_id)

    if document.variant_name == "":
        raise ValidationError("Variant name is empty")

    family = family_service.get(document.family_import_id)
    if family is None:
        raise ValidationError(f"Could not find family for {document.family_import_id}")

    return document_repo.create(db, document)


@db_session.with_transaction(__name__)
@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def delete(import_id: str, db: Session = db_session.get_db()) -> bool:
    """
    Deletes the document specified by the import_id.

    :param str import_id: The import_id of the document to delete.
    :raises RepositoryError: raised on a database error.
    :raises ValidationError: raised should the import_id be invalid.
    :return bool: True if deleted else False.
    """
    id.validate(import_id)
    return document_repo.delete(db, import_id)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def count() -> Optional[int]:
    """
    Gets a count of documents from the repository.

    :return Optional[int]: The number of documents in the repository or none.
    """
    try:
        with db_session.get_db() as db:
            return document_repo.count(db)
    except exc.SQLAlchemyError as e:
        _LOGGER.error(e)
        raise RepositoryError(str(e))
