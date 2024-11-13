import enum
from typing import Mapping

from db_client.models.organisation.authorisation import AuthAccess, AuthOperation


class AuthEndpoint(str, enum.Enum):
    """
    An Entity that can be authorized.

    NOTE: At the moment these are the upper-case plural
    version of the entity that is used in the url.
    """

    FAMILY = "FAMILIES"
    COLLECTION = "COLLECTIONS"
    DOCUMENT = "DOCUMENTS"
    CONFIG = "CONFIG"
    ANALYTICS = "ANALYTICS"
    EVENT = "EVENTS"
    INGEST = "INGEST"


AuthMap = Mapping[AuthEndpoint, Mapping[AuthOperation, AuthAccess]]

AUTH_TABLE: AuthMap = {
    # Family
    AuthEndpoint.FAMILY: {
        AuthOperation.CREATE: AuthAccess.USER,
        AuthOperation.READ: AuthAccess.USER,
        AuthOperation.UPDATE: AuthAccess.USER,
        AuthOperation.DELETE: AuthAccess.USER,
    },
    # Collection
    AuthEndpoint.COLLECTION: {
        AuthOperation.CREATE: AuthAccess.USER,
        AuthOperation.READ: AuthAccess.USER,
        AuthOperation.UPDATE: AuthAccess.USER,
        AuthOperation.DELETE: AuthAccess.USER,
    },
    # Collection
    AuthEndpoint.DOCUMENT: {
        AuthOperation.CREATE: AuthAccess.USER,
        AuthOperation.READ: AuthAccess.USER,
        AuthOperation.UPDATE: AuthAccess.USER,
        AuthOperation.DELETE: AuthAccess.USER,
    },
    # Config
    AuthEndpoint.CONFIG: {
        AuthOperation.READ: AuthAccess.USER,
    },
    # Analytics
    AuthEndpoint.ANALYTICS: {
        AuthOperation.READ: AuthAccess.USER,
    },
    # Event
    AuthEndpoint.EVENT: {
        AuthOperation.CREATE: AuthAccess.USER,
        AuthOperation.READ: AuthAccess.USER,
        AuthOperation.UPDATE: AuthAccess.USER,
        AuthOperation.DELETE: AuthAccess.USER,
    },
    # Ingest
    AuthEndpoint.INGEST: {
        AuthOperation.CREATE: AuthAccess.USER,
        AuthOperation.READ: AuthAccess.USER,
    },
}
