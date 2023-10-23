import enum
from typing import Mapping


class AuthOperation(str, enum.Enum):
    """An operation that can be authorized"""

    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


HTTP_MAP_TO_OPERATION = {
    "POST": AuthOperation.CREATE,
    "GET": AuthOperation.READ,
    "HEAD": AuthOperation.READ,
    "PUT": AuthOperation.UPDATE,
    "PATCH": AuthOperation.UPDATE,
    "DELETE": AuthOperation.DELETE,
}


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


class AuthAccess(str, enum.Enum):
    """The level of access needed"""

    USER = "USER"
    ADMIN = "ADMIN"
    SUPER = "SUPER"


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
}
