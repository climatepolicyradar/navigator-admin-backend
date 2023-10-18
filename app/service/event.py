import logging
from typing import Optional

from pydantic import ConfigDict, validate_call
from sqlalchemy import exc
from sqlalchemy.orm import Session

import app.clients.db.session as db_session
import app.repository.event as event_repo
import app.service.family as family_service
from app.errors import RepositoryError, ValidationError
from app.model.event import EventCreateDTO, EventReadDTO
from app.service import id


_LOGGER = logging.getLogger(__name__)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def get(import_id: str) -> Optional[EventReadDTO]:
    """
    Gets a family event given the import_id.

    :param str import_id: The import_id to use to get the event.
    :raises RepositoryError: raised on a database error.
    :raises ValidationError: raised should the import_id be invalid.
    :return Optional[EventReadDTO]: The event found or None.
    """
    validate_import_id(import_id)
    try:
        with db_session.get_db() as db:
            return event_repo.get(db, import_id)
    except exc.SQLAlchemyError as e:
        _LOGGER.error(e)
        raise RepositoryError(str(e))


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def all() -> list[EventReadDTO]:
    """
    Gets the entire list of family events from the repository.

    :return list[EventReadDTO]: The list of family events.
    """
    with db_session.get_db() as db:
        return event_repo.all(db)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def search(search_term: str) -> Optional[list[EventReadDTO]]:
    """
    Search for all family events that match a search term.

    Specifically searches the event title and event type name for the
    search term.

    :param str search_term: Search pattern to match.
    :return Optional[list[EventReadDTO]] The list of events that match
        the search term or none.
    """
    with db_session.get_db() as db:
        return event_repo.search(db, search_term)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def validate_import_id(import_id: str) -> None:
    """
    Validates the import id for a event.

    TODO: add more validation

    :param str import_id: import id to check.
    :raises ValidationError: raised should the import_id be invalid.
    """
    id.validate(import_id)


@db_session.with_transaction(__name__)
@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def create(event: EventCreateDTO, db: Session = db_session.get_db()) -> str:
    """
        Creates a new document with the values passed.

        :param documentDTO document: The values for the new document.
        :raises RepositoryError: raised on a database error
        :raises ValidationError: raised should the import_id be invalid.
        :return Optional[documentDTO]: The new created document or
    None if unsuccessful.
    """
    id.validate(event.family_import_id)

    family = family_service.get(event.family_import_id)
    if family is None:
        raise ValidationError(f"Could not find event for {event.family_import_id}")

    return event_repo.create(db, event)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def count() -> Optional[int]:
    """
    Gets a count of events from the repository.

    :return Optional[int]: A count of events in the repository or none.
    """
    try:
        with db_session.get_db() as db:
            return event_repo.count(db)
    except exc.SQLAlchemyError as e:
        _LOGGER.error(e)
        raise RepositoryError(str(e))
