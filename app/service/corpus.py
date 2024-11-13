import logging
from typing import Optional, Union

from pydantic import ConfigDict, validate_call
from sqlalchemy import exc
from sqlalchemy.orm import Session

import app.clients.db.session as db_session
import app.repository.corpus as corpus_repo
from app.errors import RepositoryError, ValidationError
from app.model.corpus import CorpusReadDTO, CorpusWriteDTO
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


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def validate_import_id(import_id: str) -> None:
    """
    Validates the import id for a corpus.

    :param str import_id: import id to check.
    :raises ValidationError: raised should the import_id be invalid.
    """
    id.validate(import_id)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def get(import_id: str) -> Optional[CorpusReadDTO]:
    """
    Gets a corpus given the import_id.

    :param str import_id: The import_id to use to get the corpus.
    :raises RepositoryError: raised on a database error.
    :raises ValidationError: raised should the import_id be invalid.
    :return Optional[CorpusReadDTO]: The corpus found or None.
    """
    validate_import_id(import_id)
    try:
        with db_session.get_db() as db:
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

    entity_org_id: int = get_corpus_org_id(import_id, db)
    app_user.raise_if_unauthorised_to_make_changes(user, entity_org_id, import_id)

    try:
        if corpus_repo.update(db, import_id, corpus):
            db.commit()
        else:
            db.rollback()
    except Exception as e:
        db.rollback()
        raise e
    return get(import_id)
