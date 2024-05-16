import logging

from pydantic import ConfigDict, validate_call
from sqlalchemy import exc

import app.clients.db.session as db_session
import app.repository.config as config_repo
from app.errors import RepositoryError
from app.model.config import ConfigReadDTO
from app.service import app_user

_LOGGER = logging.getLogger(__name__)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def get(user_email: str) -> ConfigReadDTO:
    """
    Gets the config

    :raises RepositoryError: If there is an issue getting the config
    :return ConfigReadDTO: The config for the application
    """

    try:
        with db_session.get_db() as db:
            # Get the organisation from the user's email
            org_id = app_user.get_organisation(db, user_email)

            return config_repo.get(db, org_id)

    except exc.SQLAlchemyError:
        _LOGGER.exception("Error while getting config")
        raise RepositoryError("Could not get the config")
