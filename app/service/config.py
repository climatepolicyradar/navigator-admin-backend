import logging
from app.errors import RepositoryError
from app.model.config import ConfigReadDTO
import app.repository.config as config_repo

from sqlalchemy import exc
import navigator_db_client.session as db_session


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
