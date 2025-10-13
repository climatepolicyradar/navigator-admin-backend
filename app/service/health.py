from app.clients.db.session import get_db


def is_database_online() -> bool:
    """
    Checks database health.

    TODO: More comprehensive health checks
    """
    with get_db() as db:
        return db.execute("SELECT 1") is not None
