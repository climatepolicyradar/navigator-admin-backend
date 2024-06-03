"""Endpoints for managing the Analytics service."""

import logging

from fastapi import APIRouter, HTTPException, Request, status

import app.service.analytics as analytics_service
from app.errors import RepositoryError
from app.model.analytics import SummaryDTO

analytics_router = r = APIRouter()

_LOGGER = logging.getLogger(__name__)


@r.get("/analytics/summary", response_model=SummaryDTO)
async def get_analytics_summary(request: Request) -> SummaryDTO:
    """
    Returns an analytics summary.

    :return dict[str, int]: returns a dictionary of the summarised analytics
    data in key (str): value (int) form.
    """
    try:
        summary_dto = analytics_service.summary(request.state.user.email)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )

    if any(summary_value is None for _, summary_value in summary_dto):
        msg = "Analytics summary not found"
        _LOGGER.error(msg)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=msg,
        )

    return summary_dto
