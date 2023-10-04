"""
Analytics Service

This layer uses the document, family, and collection repos to handle querying
the count of available entities.
"""
import logging
from typing import Optional

from pydantic import ConfigDict, validate_call
from app.errors import RepositoryError
from app.model.analytics import SummaryDTO
from app.repository import collection_repo, family_repo, document_repo
import app.clients.db.session as db_session
from sqlalchemy import exc

from app.model.analytics import SummaryDTO


_LOGGER = logging.getLogger(__name__)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def summary() -> Optional[SummaryDTO]:
    """
    Gets an analytics summary from the repository.

    :return SummaryDTO: The analytics summary found.
    """
    try:
        with db_session.get_db() as db:
            n_collections = collection_repo.count(db)
            n_families = family_repo.count(db)
            n_documents = document_repo.count(db)
            n_events = 0

        return SummaryDTO(
            n_documents=n_documents,
            n_families=n_families,
            n_collections=n_collections,
            n_events=n_events,
        )

    except exc.SQLAlchemyError as e:
        _LOGGER.error(e)
        raise RepositoryError(str(e))
