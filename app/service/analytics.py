"""
Analytics Service

This layer uses the document, family, and collection repos to handle querying
the count of available entities.
"""

import logging

from pydantic import ConfigDict, validate_call
from sqlalchemy import exc

import app.clients.db.session as db_session
import app.repository.collection as collection_repo
import app.repository.document as document_repo
import app.repository.event as event_repo
import app.repository.family as family_repo
import app.service.app_user as app_user_service
from app.errors import RepositoryError
from app.model.analytics import SummaryDTO
from app.model.user import UserContext

_LOGGER = logging.getLogger(__name__)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def summary(user: UserContext) -> SummaryDTO:
    """
    Gets an analytics summary from the repository.

    :param user_email str: The email address of the current user.
    :return SummaryDTO: The analytics summary found.
    """
    try:
        with db_session.get_db() as db:
            org_id = app_user_service.restrict_entities_to_user_org(user)
            n_collections = collection_repo.count(db, org_id)
            n_families = family_repo.count(db, org_id)
            n_documents = document_repo.count(db, org_id)
            n_events = event_repo.count(db, org_id)

            return SummaryDTO(
                n_documents=n_documents,
                n_families=n_families,
                n_collections=n_collections,
                n_events=n_events,
            )

    except exc.SQLAlchemyError as e:
        _LOGGER.error(e)
        raise RepositoryError(str(e))
