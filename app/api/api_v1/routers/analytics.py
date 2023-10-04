"""Endpoints for managing the Analytics service."""
import logging
from fastapi import APIRouter

analytics_router = r = APIRouter()

_LOGGER = logging.getLogger(__name__)


@r.get(
    "/analytics/summary",
    response_model=dict[str, int],
)
async def get_analytics_summary() -> dict[str, int]:
    """
    Returns an analytics summary.

    :return dict[str, int]: returns a dictionary of the summarised analytics
    data in key (str): value (int) form.
    """
    return {
        "n_documents": 1000,
        "n_families": 800,
        "n_collections": 10,
        "n_events": 50,
    }
