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


class AuthEntity(str, enum.Enum):
    """
    An Entity that can be authorized.

    NOTE: At the moment these are the upper-case plural
    version of the entity that is used in the url.
    """

    FAMILY = "FAMILIES"
    COLLECTION = "COLLECTIONS"


class AuthAccess(str, enum.Enum):
    """The level of access needed"""

    USER = "USER"
    ADMIN = "ADMIN"
    SUPER = "SUPER"


AuthMap = Mapping[AuthEntity, Mapping[AuthOperation, AuthAccess]]

AUTH_TABLE: AuthMap = {
    # Family
    AuthEntity.FAMILY: {
        AuthOperation.CREATE: AuthAccess.USER,
        AuthOperation.READ: AuthAccess.USER,
        AuthOperation.UPDATE: AuthAccess.USER,
        AuthOperation.DELETE: AuthAccess.ADMIN,
    },
    # Collection
    AuthEntity.COLLECTION: {
        AuthOperation.CREATE: AuthAccess.USER,
        AuthOperation.READ: AuthAccess.USER,
        AuthOperation.UPDATE: AuthAccess.USER,
        AuthOperation.DELETE: AuthAccess.ADMIN,
    },
}
