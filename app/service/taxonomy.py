import logging

from db_client.functions.corpus_helpers import get_taxonomy_by_corpus_type_name
from sqlalchemy import exc

import app.clients.db.session as db_session
from app.errors import RepositoryError

_LOGGER = logging.getLogger(__name__)


def get(corpus_type_name: str):
    """
    Gets a taxonomy for the given corpus_type_name.

    :param str corpus_type_name: The corpus_type_name to use to get the taxonomy.
    :raises RepositoryError: raised on a database error.
    :raises ValidationError: raised should the import_id be invalid.
    """
    try:
        with db_session.get_db_session() as db:
            return get_taxonomy_by_corpus_type_name(db, corpus_type_name)
    except exc.SQLAlchemyError as e:
        _LOGGER.error(e)
        raise RepositoryError(str(e))
