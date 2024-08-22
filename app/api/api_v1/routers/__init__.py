from app.api.api_v1.routers.analytics import analytics_router
from app.api.api_v1.routers.auth import auth_router
from app.api.api_v1.routers.collection import collections_router
from app.api.api_v1.routers.config import config_router
from app.api.api_v1.routers.document import document_router
from app.api.api_v1.routers.event import event_router
from app.api.api_v1.routers.family import families_router
from app.api.api_v1.routers.ingest import ingest_router

__all__ = (
    "analytics_router",
    "auth_router",
    "collections_router",
    "config_router",
    "document_router",
    "event_router",
    "families_router",
    "ingest_router",
)
