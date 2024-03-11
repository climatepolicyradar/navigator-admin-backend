import logging

from sqlalchemy import exc

import app.clients.db.session as db_session
import app.repository.config as config_repo
from app.errors import RepositoryError
from app.model.config import ConfigReadDTO

_LOGGER = logging.getLogger(__name__)


def get() -> ConfigReadDTO:
    """
    Gets the config

    :raises RepositoryError: If there is an issue getting the config
    :return ConfigReadDTO: The config for the application
    """
    try:
        with db_session.get_db() as db:
            return config_repo.get(db)
    except exc.SQLAlchemyError:
        _LOGGER.exception("Error while getting config")
        raise RepositoryError("Could not get the config")
