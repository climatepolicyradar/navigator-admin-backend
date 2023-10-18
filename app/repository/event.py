"""Operations on the repository for the Family entity."""

import logging
from datetime import datetime
from typing import Optional, Tuple, cast

from sqlalchemy import or_, Column
from sqlalchemy.orm import Query, Session
from sqlalchemy.exc import NoResultFound
from sqlalchemy_utils import escape_like

from app.clients.db.models.app.counters import CountedEntity
from app.clients.db.models.law_policy import (
    EventStatus,
    FamilyEvent,
    Family,
    FamilyDocument,
)
from app.errors import ValidationError
from app.model.event import EventCreateDTO, EventReadDTO
from app.repository import family as family_repo
from app.repository.helpers import generate_import_id


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


def _event_to_dto(family_event_meta: FamilyEventTuple) -> EventReadDTO:
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


def _dto_to_event_dict(dto: EventCreateDTO) -> dict:
    return {
        "family_import_id": dto.family_import_id,
        "family_document_import_id": dto.family_document_import_id,
        "date": dto.date,
        "title": dto.event_title,
        "event_type_name": dto.event_type_value,
        "status": EventStatus.OK,
    }


def _event_from_dto(db: Session, dto: EventCreateDTO):
    family_event = FamilyEvent(**_dto_to_event_dict(dto))
    return family_event


def all(db: Session) -> list[EventReadDTO]:
    """
    Returns all family events.

    :param db Session: The database connection.
    :return Optional[EventReadDTO]: All family events in the database.
    """
    family_event_metas = _get_query(db).all()

    if not family_event_metas:
        return []

    result = [_event_to_dto(event_meta) for event_meta in family_event_metas]
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

    return _event_to_dto(family_event_meta)


def search(db: Session, search_term: str) -> Optional[list[EventReadDTO]]:
    """
    Get family events matching a search term on the event title or type.

    :param db Session: The database connection.
    :param str search_term: Any search term to filter on the event title
        or event type name.
    :return Optional[list[EventReadDTO]]: A list of matching family
        events or none.
    """
    term = f"%{escape_like(search_term)}%"
    search = or_(FamilyEvent.title.ilike(term), FamilyEvent.event_type_name.ilike(term))

    try:
        found = _get_query(db).filter(search).all()
    except NoResultFound as e:
        _LOGGER.error(e)
        return

    if not found:
        return []

    return [_event_to_dto(f) for f in found]


def create(db: Session, event: EventCreateDTO) -> str:
    """
    Creates a new family event.

    :param db Session: The database connection.
    :param EventCreateDTO event: The values for the new event.
    :return str: The import id of the newly created family event.
    """

    try:
        new_family_event = _event_from_dto(db, event)

        family_import_id = new_family_event.family_import_id

        # Generate the import_id for the new event
        org = family_repo.get_organisation(db, cast(str, family_import_id))
        if org is None:
            raise ValidationError(
                f"Cannot find counter to generate id for {family_import_id}"
            )

        org_name = cast(str, org.name)
        new_family_event.import_id = cast(
            Column, generate_import_id(db, CountedEntity.Event, org_name)
        )

        db.add(new_family_event)
        db.flush()
    except Exception:
        _LOGGER.exception("Error trying to create Event")
        raise

    return cast(str, new_family_event.import_id)


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
