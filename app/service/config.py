import logging

from pydantic import ConfigDict, validate_call
from sqlalchemy import exc

import app.clients.db.session as db_session
import app.repository.config as config_repo
from app.errors import RepositoryError
from app.model.config import ConfigReadDTO
from app.model.jwt_user import UserContext

_LOGGER = logging.getLogger(__name__)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def get(user: UserContext) -> ConfigReadDTO:
    """
    Gets the config

    :raises RepositoryError: If there is an issue getting the config
    :return ConfigReadDTO: The config for the application
    """
    try:
        with db_session.get_db() as db:
            return config_repo.get(db, user)

    except exc.SQLAlchemyError:
        _LOGGER.exception("Error while getting config")
        raise RepositoryError("Could not get the config")
