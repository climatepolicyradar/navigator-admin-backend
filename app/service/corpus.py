import logging
from typing import Optional, Union

from pydantic import ConfigDict, validate_call
from sqlalchemy import exc
from sqlalchemy.orm import Session

import app.clients.db.session as db_session
import app.repository.corpus as corpus_repo
import app.repository.document_file as file_repo
import app.repository.organisation as org_repo
from app.clients.aws.client import get_s3_client
from app.errors import ConflictError, RepositoryError, ValidationError
from app.model.corpus import (
    CorpusCreateDTO,
    CorpusLogoUploadDTO,
    CorpusReadDTO,
    CorpusWriteDTO,
)
from app.model.user import UserContext
from app.service import app_user, id

_LOGGER = logging.getLogger(__name__)


def get_corpus_org_id(corpus_import_id: str, db: Optional[Session] = None) -> int:
    """Get the organisation ID a corpus belongs to.

    :param Session db: The DB session to connect to.
    :param str corpus_id: The corpus import ID we want to get the org
        for.
    :return Optional[int]: Return the organisation ID the given corpus
        belongs to or None.
    """
    if db is None:
        db = db_session.get_db()

    org_id = corpus_repo.get_corpus_org_id(db, corpus_import_id)
    if org_id is None:
        msg = f"No organisation associated with corpus {corpus_import_id}"
        _LOGGER.error(msg)
        raise ValidationError(msg)
    return org_id


def validate(db: Session, corpus_import_id: str) -> bool:
    """Validate whether a corpus with the given ID exists in the DB.

    :param Session db: The DB session to connect to.
    :param str corpus_id: The corpus import ID we want to validate.
    :raises ValidationError: When the corpus ID is not found in the DB.
    :raises RepositoryError: When an error occurs.
    :return bool: Return whether or not the corpus exists in the DB.
    """
    try:
        if corpus_repo.verify_corpus_exists(db, corpus_import_id):
            return True

    except Exception as e:
        _LOGGER.error(e)
        raise RepositoryError(e)

    msg = f"Corpus '{corpus_import_id}' not found"
    _LOGGER.error(msg)
    raise ValidationError(msg)


def validate_list(db: Session, corpus_import_ids: list[str]) -> bool:
    """Validate whether a list of corpora exists in the DB.

    :param Session db: The DB session to connect to.
    :param list[str] corpus_import_ids: The corpus import IDs we want to
        validate.
    :raises ValidationError: When one or more of the corpus IDs are not
        found in the DB.
    :raises RepositoryError: When an error occurs.
    :return bool: Return whether or not all the corpus exists in the DB.
    """
    try:
        missing_ids = [
            import_id
            for import_id in corpus_import_ids
            if not corpus_repo.verify_corpus_exists(db, import_id)
        ]
        if missing_ids:
            _LOGGER.debug(f"Missing corpus IDs: {missing_ids}")
            return False
        return True
    except Exception as e:
        _LOGGER.error(e)
        raise RepositoryError(e)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def validate_import_id(import_id: str, db: Optional[Session] = None) -> None:
    """Validate the import id for a corpus.

    :param str import_id: import id to check.
    :param Optional[Session] db: The DB session to connect to.
    :raises ValidationError: raised should the import_id be invalid.
    """
    if db is None:
        db = db_session.get_db()

    id.validate(import_id)

    # Validate the first part contains either the org name or type.
    id_parts = import_id.split(".")
    if (
        id_parts[0] not in org_repo.get_distinct_org_options(db)
        or id_parts[1] != "corpus"
    ):
        raise ValidationError(f"The import id {import_id} is invalid!")


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def get(import_id: str, db: Optional[Session] = None) -> Optional[CorpusReadDTO]:
    """
    Gets a corpus given the import_id.

    :param str import_id: The import_id to use to get the corpus.
    :param Optional[Session] db: The DB session to connect to.
    :raises RepositoryError: raised on a database error.
    :raises ValidationError: raised should the import_id be invalid.
    :return Optional[CorpusReadDTO]: The corpus found or None.
    """
    if db is None:
        db = db_session.get_db()

    validate_import_id(import_id, db)
    try:
        return corpus_repo.get(db, import_id)
    except exc.SQLAlchemyError as e:
        _LOGGER.error(e)
        raise RepositoryError(str(e))


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def all(user: UserContext) -> list[CorpusReadDTO]:
    """
    Gets the entire list of corpora from the repository.

    :param UserContext user: The current user context.
    :return list[CorpusReadDTO]: The list of corpora.
    """
    with db_session.get_db() as db:
        org_id = app_user.restrict_entities_to_user_org(user)
        return corpus_repo.all(db, org_id)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def search(
    query_params: dict[str, Union[str, int]], user: UserContext
) -> list[CorpusReadDTO]:
    """
    Searches for the search term against corpora on specified fields.

    Where 'q' is used instead of an explicit field name, only the titles
    of all the corpora are searched for the given term.

    :param dict query_params: Search patterns to match against specified
        fields, given as key value pairs in a dictionary.
    :param UserContext user: The current user context.
    :return list[CorpusReadDTO]: The list of corpora matching the
        given search terms.
    """
    with db_session.get_db() as db:
        org_id = app_user.restrict_entities_to_user_org(user)
        return corpus_repo.search(db, query_params, org_id)


@db_session.with_database()
@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def update(
    import_id: str,
    corpus: CorpusWriteDTO,
    user: UserContext,
    db: Optional[Session] = None,
) -> Optional[CorpusReadDTO]:
    """
    Updates a single corpus with the values passed.

    :param str import_id: The import ID of the corpus to update.
    :param CorpusWriteDTO corpus: The DTO with all the values to change (or keep).
    :param UserContext user: The current user context.
    :raises AuthorisationError: raised if user has incorrect permissions.
    :raises RepositoryError: raised on a database error.
    :raises ValidationError: raised should the import_id be invalid.
    :return Optional[CorpusReadDTO]: The updated corpus or None if not updated.
    """
    validate_import_id(import_id)

    if db is None:
        db = db_session.get_db()

    original_corpus = get(import_id)
    if original_corpus is None:
        return None

    try:
        if corpus_repo.update(db, import_id, corpus):
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
    corpus: CorpusCreateDTO,
    user: UserContext,
    db: Optional[Session] = None,
) -> str:
    """Create a new Corpus from the values passed.

    :param CorpusCreateDTO corpus: The values for the new Family.
    :param UserContext user: The current user context.
    :raises RepositoryError: raised on a database error
    :raises ValidationError: raised should the import_id be invalid.
    :return str: The new created Corpus or None if unsuccessful.
    """
    if db is None:
        db = db_session.get_db()

    # Check the corpus type name exists in the database already.
    if not corpus_repo.is_corpus_type_name_valid(db, corpus.corpus_type_name):
        raise ValidationError("Invalid corpus type name")

    # Check that the organisation ID exists in the database.
    if org_repo.get_name_from_id(db, corpus.organisation_id) is None:
        raise ValidationError("Invalid organisation")

    if corpus.import_id is not None:
        validate_import_id(corpus.import_id, db)

        corpus_exists = get(corpus.import_id)
        if corpus_exists is not None:
            raise ConflictError(f"Corpus '{corpus.import_id}' already exists")

    try:
        import_id = corpus_repo.create(db, corpus)
        if len(import_id) == 0:
            db.rollback()
        return import_id
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.commit()


def get_upload_url(corpus_id: str) -> CorpusLogoUploadDTO:
    """Get a presigned URL for uploading a corpus logo.

    :param corpus_id: The ID of the corpus to upload a logo for
    :param user_context: The user context from the request
    :return: Upload URLs for the logo
    """
    # Generate a key for the logo in S3
    key = f"corpora/{corpus_id}/logo.png"

    # Get the S3 client
    client = get_s3_client()

    # Get the upload URLs
    presigned_url, cdn_url = file_repo.get_upload_details(client, key)

    return CorpusLogoUploadDTO(presigned_upload_url=presigned_url, cdn_url=cdn_url)
