"""Operations on the repository for the Family entity."""

import logging
from datetime import datetime
from typing import Optional, Tuple, cast

from sqlalchemy import or_
from sqlalchemy.orm import Query, Session
from sqlalchemy.exc import NoResultFound
from sqlalchemy_utils import escape_like

from app.clients.db.models.law_policy import (
    EventStatus,
    FamilyEvent,
    Family,
    FamilyDocument,
)
from app.model.event import EventReadDTO


_LOGGER = logging.getLogger(__name__)

FamilyEventTuple = Tuple[FamilyEvent, Family, FamilyDocument]


def _get_query(db: Session) -> Query:
    # NOTE: SqlAlchemy will make a complete hash of the query generation
    #       if columns are used in the query() call. Therefore, entire
    #       objects are returned.
    return (
        db.query(FamilyEvent, Family, FamilyDocument)
        .filter(FamilyEvent.family_import_id == Family.import_id)
        .join(
            FamilyDocument,
            FamilyDocument.family_import_id == FamilyEvent.family_document_import_id,
            isouter=True,
        )
    )


def _event_to_dto(db: Session, family_event_meta: FamilyEventTuple) -> EventReadDTO:
    family_event = family_event_meta[0]

    family_document_import_id = (
        None
        if family_event.family_document_import_id is None
        else cast(str, family_event.family_document_import_id)
    )

    return EventReadDTO(
        import_id=cast(str, family_event.import_id),
        event_title=cast(str, family_event.title),
        date=cast(datetime, family_event.date),
        family_import_id=cast(str, family_event.family_import_id),
        family_document_import_id=family_document_import_id,
        event_type_value=cast(str, family_event.event_type_name),
        event_status=cast(EventStatus, family_event.status),
    )


def all(db: Session) -> list[EventReadDTO]:
    """
    Returns all family events.

    :param db Session: The database connection.
    :return Optional[EventReadDTO]: All family events in the database.
    """
    family_event_metas = _get_query(db).all()

    if not family_event_metas:
        return []

    result = [_event_to_dto(db, event_meta) for event_meta in family_event_metas]
    return result


def get(db: Session, import_id: str) -> Optional[EventReadDTO]:
    """
    Gets a single family event from the repository.

    :param db Session: The database connection.
    :param str import_id: The import_id of the event.
    :return Optional[EventReadDTO]: A single family event or nothing.
    """
    try:
        family_event_meta = (
            _get_query(db).filter(FamilyEvent.import_id == import_id).one()
        )
    except NoResultFound as e:
        _LOGGER.error(e)
        return

    return _event_to_dto(db, family_event_meta)


def search(db: Session, search_term: str) -> list[EventReadDTO]:
    """
    Get family events matching a search term on the event title or type.

    :param db Session: The database connection.
    :param str search_term: Any search term to filter on the event title
        or event type name.
    :return list[EventReadDTO]: A list of matching family events.
    """
    term = f"%{escape_like(search_term)}%"
    search = or_(FamilyEvent.title.ilike(term), FamilyEvent.event_type_name.ilike(term))
    found = _get_query(db).filter(search).all()

    if not found:
        return []

    return [_event_to_dto(db, f) for f in found]


def count(db: Session) -> Optional[int]:
    """
    Counts the number of family events in the repository.

    :param db Session: The database connection.
    :return Optional[int]: The number of family events in the repository
        or nothing.
    """
    try:
        n_events = _get_query(db).count()
    except NoResultFound as e:
        _LOGGER.error(e)
        return

    return n_events
