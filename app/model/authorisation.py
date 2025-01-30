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
    BULK_IMPORT = "BULK-IMPORT"
    CORPUS = "CORPORA"
    CORPUS_TYPE = "CORPUS-TYPES"
    ORGANISATION = "ORGANISATIONS"


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
    # Bulk Import
    AuthEndpoint.BULK_IMPORT: {
        AuthOperation.CREATE: AuthAccess.SUPER,
        AuthOperation.READ: AuthAccess.SUPER,
    },
    # Corpus
    AuthEndpoint.CORPUS: {
        AuthOperation.CREATE: AuthAccess.SUPER,
        AuthOperation.READ: AuthAccess.SUPER,
        AuthOperation.UPDATE: AuthAccess.SUPER,
    },
    # Corpus Type
    AuthEndpoint.CORPUS_TYPE: {
        AuthOperation.CREATE: AuthAccess.SUPER,
        AuthOperation.READ: AuthAccess.SUPER,
    },
    # Organisation
    AuthEndpoint.ORGANISATION: {
        AuthOperation.READ: AuthAccess.SUPER,
    },
}
