"""
Analytics Service

This layer uses the document, family, and collection repos to handle querying
the count of available entities.
"""
import logging

from pydantic import ConfigDict, validate_call
from sqlalchemy import exc

from app.clients.db.errors import RepositoryError
from app.model.analytics import SummaryDTO
import app.service.collection as collection_service
import app.service.document as document_service
import app.service.family as family_service
import app.service.event as event_service


_LOGGER = logging.getLogger(__name__)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def summary() -> SummaryDTO:
    """
    Gets an analytics summary from the repository.

    :return SummaryDTO: The analytics summary found.
    """
    try:
        n_collections = collection_service.count()
        n_families = family_service.count()
        n_documents = document_service.count()
        n_events = event_service.count()

        return SummaryDTO(
            n_documents=n_documents,
            n_families=n_families,
            n_collections=n_collections,
            n_events=n_events,
        )

    except exc.SQLAlchemyError as e:
        _LOGGER.error(e)
        raise RepositoryError(str(e))
