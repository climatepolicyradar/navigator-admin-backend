import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.errors import RepositoryError, ValidationError
from app.repository import corpus_repo

_LOGGER = logging.getLogger(__name__)


def get_corpus_org_id(db: Session, corpus_import_id: str) -> Optional[int]:
    """Get the organisation ID(s) a corpus belongs to.

    TODO: Will need to review as part of PDCT-1011.

    :param Session db: The DB session to connect to.
    :param str corpus_id: The corpus import ID we want to get the org
        for.
    :return Optional[int]: Return the organisation ID the given corpus
        belongs to or None.
    """
    org_id = corpus_repo.get_corpus_org_id(db, corpus_import_id)
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
        is_valid = corpus_repo.validate(db, corpus_import_id)
        if is_valid:
            return is_valid

    except Exception as e:
        _LOGGER.error(e)
        raise RepositoryError(e)

    msg = f"Corpus '{corpus_import_id}' not found"
    _LOGGER.error(msg)
    raise ValidationError(msg)
