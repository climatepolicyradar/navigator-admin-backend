import logging
import os
import subprocess
from datetime import datetime

from app.config import (
    ADMIN_POSTGRES_DATABASE,
    ADMIN_POSTGRES_HOST,
    ADMIN_POSTGRES_PASSWORD,
    ADMIN_POSTGRES_USER,
)

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)


def get_database_dump() -> str:
    """
    Dumps the PostgreSQL database to a local SQL file.

    Generates a timestamped `.sql` file using `pg_dump` and stores it
    in the current working directory.

    :raises subprocess.CalledProcessError: If the `pg_dump` command fails.
    :return str: The path to the generated SQL dump file.
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

    # Set environment with password
    env = {**os.environ, "PGPASSWORD": ADMIN_POSTGRES_PASSWORD}

    try:
        _LOGGER.info(f"Starting database dump to {dump_file}")
        result = subprocess.run(
            cmd,
            check=True,
            env=env,
            capture_output=True,
            text=True,
        )
        _LOGGER.info("Database dump completed successfully")
        _LOGGER.debug(f"pg_dump output: {result.stdout}")
        return dump_file

    except subprocess.CalledProcessError as e:
        _LOGGER.error(f"Database dump failed: {e}")
        _LOGGER.error(f"stderr: {e.stderr}")
        raise


# TODO: Consider possible security implications associated with the subprocess module.
