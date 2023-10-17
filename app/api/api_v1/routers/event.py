"""Endpoints for managing Family Event entities."""
import logging

from fastapi import APIRouter, HTTPException, status

import app.service.event as event_service
from app.errors import RepositoryError, ValidationError
from app.model.event import EventReadDTO

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
async def search_event(q: str = "") -> list[EventReadDTO]:
    """
    Searches for family events matching the "q" URL parameter.

    :param str q: The string to match, defaults to ""
    :raises HTTPException: If nothing found a 404 is returned.
    :return list[EventDTO]: A list of matching events.
    """
    events_found = event_service.search(q)

    if not events_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Events not found for term: {q}",
        )

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
