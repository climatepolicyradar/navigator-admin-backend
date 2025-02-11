from app.api.api_v1.routers.analytics import analytics_router
from app.api.api_v1.routers.auth import auth_router
from app.api.api_v1.routers.bulk_import import bulk_import_router
from app.api.api_v1.routers.collection import collections_router
from app.api.api_v1.routers.config import config_router
from app.api.api_v1.routers.corpus import corpora_router
from app.api.api_v1.routers.corpus_type import corpus_types_router
from app.api.api_v1.routers.custom_app import custom_app_router
from app.api.api_v1.routers.document import document_router
from app.api.api_v1.routers.event import event_router
from app.api.api_v1.routers.family import families_router
from app.api.api_v1.routers.organisation import organisations_router

__all__ = (
    "analytics_router",
    "auth_router",
    "corpora_router",
    "corpus_types_router",
    "collections_router",
    "config_router",
    "custom_app_router",
    "document_router",
    "event_router",
    "families_router",
    "organisations_router",
    "bulk_import_router",
)
