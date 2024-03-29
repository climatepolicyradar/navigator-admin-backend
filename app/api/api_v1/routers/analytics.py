"""Endpoints for managing the Analytics service."""

import logging

from fastapi import APIRouter, HTTPException, status

import app.service.analytics as analytics_service
from app.errors import RepositoryError
from app.model.analytics import SummaryDTO

analytics_router = r = APIRouter()

_LOGGER = logging.getLogger(__name__)


@r.get(
    "/analytics/summary",
    response_model=SummaryDTO,
)
async def get_analytics_summary() -> SummaryDTO:
    """
    Returns an analytics summary.

    :return dict[str, int]: returns a dictionary of the summarised analytics
    data in key (str): value (int) form.
    """
    try:
        summary_dto = analytics_service.summary()
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )

    if any(summary_value is None for _, summary_value in summary_dto):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analytics summary not found",
        )

    return summary_dto
