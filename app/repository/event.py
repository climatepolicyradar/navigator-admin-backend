"""Operations on the repository for the Family entity."""

import logging
from datetime import datetime
from typing import Optional, Tuple, Union, cast

from db_client.models.app.counters import CountedEntity
from db_client.models.law_policy import EventStatus, Family, FamilyDocument, FamilyEvent
from sqlalchemy import Column, and_
from sqlalchemy import delete as db_delete
from sqlalchemy import or_
from sqlalchemy import update as db_update
from sqlalchemy.exc import NoResultFound, OperationalError
from sqlalchemy.orm import Query, Session
from sqlalchemy_utils import escape_like

from app.errors import RepositoryError, ValidationError
from app.model.event import EventCreateDTO, EventReadDTO, EventWriteDTO
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
        created=cast(datetime, family_event.created),
        last_modified=cast(datetime, family_event.last_modified),
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


def _event_from_dto(dto: EventCreateDTO):
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


def search(db: Session, query_params: dict[str, Union[str, int]]) -> list[EventReadDTO]:
    """
    Get family events matching a search term on the event title or type.

    :param db Session: The database connection.
    :param dict query_params: Any search terms to filter on specified
        fields (title & event type name by default if 'q' specified).
    :raises HTTPException: If a DB error occurs a 503 is returned.
    :raises HTTPException: If the search request times out a 408 is
        returned.
    :return list[EventReadDTO]: A list of matching family events.
    """
    search = []
    if "q" in query_params.keys():
        term = f"%{escape_like(query_params['q'])}%"
        search.append(
            or_(FamilyEvent.title.ilike(term), FamilyEvent.event_type_name.ilike(term))
        )

    condition = and_(*search) if len(search) > 1 else search[0]
    try:
        found = (
            _get_query(db).filter(condition).limit(query_params["max_results"]).all()
        )
    except OperationalError as e:
        if "canceling statement due to statement timeout" in str(e):
            raise TimeoutError
        raise RepositoryError(e)

    return [_event_to_dto(f) for f in found]


def create(db: Session, event: EventCreateDTO) -> str:
    """
    Creates a new family event.

    :param db Session: The database connection.
    :param EventCreateDTO event: The values for the new event.
    :return str: The import id of the newly created family event.
    """

    try:
        new_family_event = _event_from_dto(event)

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


def update(db: Session, import_id: str, event: EventWriteDTO) -> bool:
    """
    Updates a single entry with the new values passed.

    :param db Session: the database connection
    :param str import_id: The event import id to change.
    :param EventDTO event: The new values
    :return bool: True if new values were set otherwise false.
    """
    new_values = event.model_dump()

    original_fe = (
        db.query(FamilyEvent).filter(FamilyEvent.import_id == import_id).one_or_none()
    )

    if original_fe is None:  # Not found the event to update
        _LOGGER.error(f"Unable to find event for update {import_id}")
        return False

    result = db.execute(
        db_update(FamilyEvent)
        .where(FamilyEvent.import_id == original_fe.import_id)
        .values(
            title=new_values["event_title"],
            event_type_name=new_values["event_type_value"],
            date=new_values["date"],
        )
    )

    if result.rowcount == 0:  # type: ignore
        msg = f"Could not update event fields: {event}"
        _LOGGER.error(msg)
        raise RepositoryError(msg)

    return True


def delete(db: Session, import_id: str) -> bool:
    """
    Deletes a single event by the import id.

    :param db Session: the database connection
    :param str import_id: The event import id to delete.
    :return bool: True if deleted False if not.
    """

    found = (
        db.query(FamilyEvent).filter(FamilyEvent.import_id == import_id).one_or_none()
    )
    if found is None:
        _LOGGER.error(f"Event with id {import_id} not found")
        return False

    result = db.execute(
        db_delete(FamilyEvent).where(FamilyEvent.import_id == import_id)
    )
    if result.rowcount == 0:  # type: ignore
        msg = f"Could not delete event : {import_id}"
        _LOGGER.error(msg)
        raise RepositoryError(msg)

    return True


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
