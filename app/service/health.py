from app.clients.db.session import get_db


def is_database_online() -> bool:
    """
    Checks database health.

    TODO: More comprehensive health checks
    """

    return get_db().execute("SELECT 1") is not None
