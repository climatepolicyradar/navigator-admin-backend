import logging
from app.errors import RepositoryError
import app.repository.config as config_repo

from sqlalchemy import exc
import app.clients.db.session as db_session


_LOGGER = logging.getLogger(__name__)


def get():
    try:
        with db_session.get_db() as db:
            return config_repo.get(db)
    except exc.SQLAlchemyError:
        _LOGGER.exception("Error while getting config")
        raise RepositoryError("Could not get the config")
