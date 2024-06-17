import logging
from typing import Optional, Union

from pydantic import ConfigDict, validate_call
from sqlalchemy import exc
from sqlalchemy.orm import Session

import app.clients.db.session as db_session
import app.repository.event as event_repo
import app.service.family as family_service
from app.errors import RepositoryError, ValidationError
from app.model.event import EventCreateDTO, EventReadDTO, EventWriteDTO
from app.model.user import UserContext
from app.service import app_user, id

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
def all(user: UserContext) -> list[EventReadDTO]:
    """
    Gets the entire list of family events from the repository.

    :param UserContext user: The current user context.
    :return list[EventReadDTO]: The list of family events.
    """
    with db_session.get_db() as db:
        org_id = app_user.restrict_entities_to_user_org(user)
        return event_repo.all(db, org_id)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def search(
    query_params: dict[str, Union[str, int]], user: UserContext
) -> list[EventReadDTO]:
    """
    Searches for the search term against events on specified fields.

    Where 'q' is used instead of an explicit field name, the titles and
    event type names of all the events are searched for the given term
    only.

    :param dict query_params: Search patterns to match against specified
        fields, given as key value pairs in a dictionary.
    :param UserContext user: The current user context.
    :return list[EventReadDTO]: The list of events matching the given
        search terms.
    """
    with db_session.get_db() as db:
        org_id = app_user.restrict_entities_to_user_org(user)
        return event_repo.search(db, query_params, org_id)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def validate_import_id(import_id: str) -> None:
    """
    Validates the import id for a event.

    :param str import_id: import id to check.
    :raises ValidationError: raised should the import_id be invalid.
    """
    id.validate(import_id)


@db_session.with_database()
@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def create(event: EventCreateDTO, db: Optional[Session]) -> str:
    """
        Creates a new event with the values passed.

        :param eventDTO event: The values for the new event.
        :raises RepositoryError: raised on a database error
        :raises ValidationError: raised should the import_id be invalid.
        :return Optional[eventDTO]: The new created event or
    None if unsuccessful.
    """
    id.validate(event.family_import_id)

    if db is None:
        db = db_session.get_db()

    family = family_service.get(event.family_import_id)
    if family is None:
        raise ValidationError(
            f"Could not find family when creating event for {event.family_import_id}"
        )

    try:
        import_id = event_repo.create(db, event)
        if len(import_id) == 0:
            db.rollback()
        return import_id
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.commit()


@db_session.with_database()
@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def update(
    import_id: str,
    event: EventWriteDTO,
    db: Optional[Session],
) -> Optional[EventReadDTO]:
    """
    Updates a single event with the values passed.

    :param EventWriteDTO event: The DTO with all the values to change (or keep).
    :raises RepositoryError: raised on a database error.
    :raises ValidationError: raised should the import_id be invalid.
    :return Optional[EventReadDTO]: The updated event or None if not updated.
    """
    validate_import_id(import_id)

    if db is None:
        db = db_session.get_db()

    try:
        if event_repo.update(db, import_id, event):
            db.commit()
        else:
            db.rollback()
    except Exception as e:
        db.rollback()
        raise e
    return get(import_id)


@db_session.with_database()
@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def delete(import_id: str, user: UserContext, db: Optional[Session]) -> bool:
    """
    Deletes the event specified by the import_id.

    :param str import_id: The import_id of the event to delete.
    :param UserContext user: The current user context.
    :raises RepositoryError: raised on a database error.
    :raises ValidationError: raised should the import_id be invalid.
    :return bool: True if deleted else False.
    """
    id.validate(import_id)

    if db is None:
        db = db_session.get_db()

    event = get(import_id)
    if event is None:
        return False

    entity_org_id = get_org_from_id(db, import_id)
    app_user.raise_if_unauthorised_to_make_changes(user, entity_org_id, import_id)

    try:
        db.begin_nested()
        if result := event_repo.delete(db, import_id):
            db.commit()
        else:
            db.rollback()
        return result
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.commit()


def get_org_from_id(db: Session, import_id: str) -> int:
    org = event_repo.get_org_from_import_id(db, import_id)

    if org is None:
        msg = f"No organisation associated with import id {import_id}"
        _LOGGER.error(msg)
        raise ValidationError(msg)

    return org
