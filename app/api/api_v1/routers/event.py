"""Endpoints for managing Family Event entities."""
import logging

from fastapi import APIRouter, HTTPException, Request, status

import app.service.event as event_service
from app.api.api_v1.query_params import (
    get_query_params_as_dict,
    set_default_query_params,
    validate_query_params,
)
from app.errors import RepositoryError, ValidationError
from app.model.event import EventCreateDTO, EventReadDTO, EventWriteDTO

event_router = r = APIRouter()

_LOGGER = logging.getLogger(__name__)


@r.get(
    "/events",
    response_model=list[EventReadDTO],
)
async def get_all_events() -> list[EventReadDTO]:
    """
    Returns all family events.

    :return EventDTO: returns a EventDTO if the event is found.
    """
    found_events = event_service.all()

    if not found_events:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No family events found",
        )

    return found_events


@r.get(
    "/events/",
    response_model=list[EventReadDTO],
)
async def search_event(request: Request) -> list[EventReadDTO]:
    """
    Searches for family events matching URL parameters ("q" by default).

    :param Request request: The fields to match against and the values
        to search for. Defaults to searching for "" in event titles and
        type names.
    :raises HTTPException: If invalid fields passed a 400 is returned.
    :raises HTTPException: If a DB error occurs a 503 is returned.
    :raises HTTPException: If the search request times out a 408 is
        returned.
    :return list[EventReadDTO]: A list of matching events (which can be
        empty).
    """
    query_params = get_query_params_as_dict(request.query_params)

    DEFAULT_SEARCH_FIELDS = ["title", "event_type_value"]
    query_params = set_default_query_params(query_params, DEFAULT_SEARCH_FIELDS)

    VALID_PARAMS = ["q", "max_results"]
    validate_query_params(query_params, VALID_PARAMS)

    try:
        events_found = event_service.search(query_params)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )
    except TimeoutError:
        msg = "Request timed out fetching matching events. Try adjusting your query."
        _LOGGER.error(msg)
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=msg,
        )

    if len(events_found) == 0:
        _LOGGER.info(f"Events not found for terms: {query_params}")

    return events_found


@r.get(
    "/events/{import_id}",
    response_model=EventReadDTO,
)
async def get_event(import_id: str) -> EventReadDTO:
    """
    Returns a specific family event given an import id.

    :param str import_id: Specified import_id.
    :raises HTTPException: If the event is not found a 404 is returned.
    :return EventDTO: returns a EventDTO if the event is found.
    """
    try:
        event = event_service.get(import_id)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event not found: {import_id}",
        )

    return event


@r.post("/events", response_model=str, status_code=status.HTTP_201_CREATED)
async def create_event(
    new_event: EventCreateDTO,
) -> str:
    """
    Creates a specific event given the values in EventCreateDTO.

    :raises HTTPException: If a validation error occurs, a 400 is
        returned.
    :raises HTTPException: If an SQL alchemy database error occurs, a
        503 is returned.
    :return str: returns a the import_id of the event created.
    """
    try:
        return event_service.create(new_event)

    except ValidationError as e:
        _LOGGER.error(e.message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)

    except RepositoryError as e:
        _LOGGER.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )


@r.put(
    "/events/{import_id}",
    response_model=EventReadDTO,
)
async def update_event(
    import_id: str,
    new_event: EventWriteDTO,
) -> EventReadDTO:
    """
    Updates a specific event given the import id.

    :param str import_id: Specified import_id.
    :raises HTTPException: If the event is not found a 404 is returned.
    :return EventDTO: returns a EventDTO of the event updated.
    """
    try:
        event = event_service.update(import_id, new_event)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )

    if event is None:
        detail = f"Event not updated: {import_id}"
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

    return event


@r.delete(
    "/events/{import_id}",
)
async def delete_event(
    import_id: str,
) -> None:
    """
    Deletes a specific event given the import id.

    :param str import_id: Specified import_id.
    :raises HTTPException: If the event is not found a 404 is returned.
    """
    try:
        event_deleted = event_service.delete(import_id)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )

    if not event_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event not deleted: {import_id}",
        )
