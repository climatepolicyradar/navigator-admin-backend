import logging
import subprocess
from datetime import datetime

from app.config import ADMIN_POSTGRES_DATABASE, ADMIN_POSTGRES_HOST, ADMIN_POSTGRES_USER

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)


def get_database_dump() -> str:
    """
    Dump the PostgreSQL database to a file.

    Returns:
        str: Path to the dump file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dump_file = f"navigator_dump_{timestamp}.sql"

    # pg_dump command
    cmd = [
        "pg_dump",
        "-h",
        ADMIN_POSTGRES_HOST,
        "-U",
        ADMIN_POSTGRES_USER,
        "-d",
        ADMIN_POSTGRES_DATABASE,
        "-f",
        dump_file,
    ]

    try:
        _LOGGER.info(f"Starting database dump to {dump_file}")
        subprocess.run(cmd, check=True)
        _LOGGER.info("Database dump completed successfully")
        return dump_file
    except subprocess.CalledProcessError as e:
        _LOGGER.error(f"Database dump failed: {e}")
        raise
