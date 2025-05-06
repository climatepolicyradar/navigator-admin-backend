import logging
import re
import subprocess
from datetime import datetime
from pathlib import Path

from app.config import (
    ADMIN_POSTGRES_DATABASE,
    ADMIN_POSTGRES_HOST,
    ADMIN_POSTGRES_PASSWORD,
    ADMIN_POSTGRES_USER,
)

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)


def validate_postgres_param(value: str) -> str:
    """
    Allow only alphanumeric, dots, underscores and hyphens in Postgres parameters.

    :param value: The Postgres parameter to validate
    returns str: The validated parameter
    :raises ValueError: If the parameter is invalid
    """
    if value is None or not re.match(r"^[\w.-]+$", value):
        raise ValueError(f"Invalid Postgres parameter: {value}")
    return value


def delete_local_file(file_path: str) -> None:
    """Delete a local file safely, logging any issues."""
    path = Path(file_path)

    try:
        if path.exists():
            path.unlink()
            _LOGGER.debug(f"Deleted local file: {file_path}")
    except Exception as e:
        _LOGGER.error(f"⚠️ Failed to delete file {file_path}: {e}")
        raise e


def get_database_dump(timeout_secs: int = 300) -> str:
    """
    Dumps the PostgreSQL database to a local SQL file.

    Generates a timestamped `.sql` file using `pg_dump` and stores it
    in the current working directory with secure permissions.

    :param timeout_secs int: Timeout for the pg_dump command in seconds (default is 300)

    :raises subprocess.CalledProcessError: If the `pg_dump` command fails.
    :raises RuntimeError: If security checks fail or the operation times out.
    :return str: The path to the generated SQL dump file.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dump_file = Path(f"navigator_dump_{timestamp}.sql")

    if dump_file.exists():
        raise RuntimeError(f"Dump file already exists: {dump_file}")

    # pg_dump command
    cmd = [
        "pg_dump",
        "--no-password",  # Force password to come from environment only
        "-h",
        validate_postgres_param(ADMIN_POSTGRES_HOST),
        "-U",
        validate_postgres_param(ADMIN_POSTGRES_USER),
        "-d",
        validate_postgres_param(ADMIN_POSTGRES_DATABASE),
        "-f",
        str(dump_file),
    ]

    # Set environment with password
    env = {"PGPASSWORD": ADMIN_POSTGRES_PASSWORD}

    try:
        _LOGGER.info(f"🚀 Starting database dump to {dump_file}")

        result = subprocess.run(
            cmd,
            check=True,
            env=env,
            capture_output=True,
            text=True,
            shell=False,
            timeout=timeout_secs,
        )

        # Set restrictive permissions on the dump file
        file_permissions = 0o600
        dump_file.chmod(file_permissions)

        _LOGGER.info("✅ Database dump completed successfully")
        if result.stdout:
            _LOGGER.debug(f"pg_dump output: {result.stdout}")
        return str(dump_file)

    except subprocess.TimeoutExpired:
        _LOGGER.error("⌛ Database dump timed out")
        if dump_file.exists():
            dump_file.unlink()
        raise RuntimeError(f"Database dump timed out after {timeout_secs} seconds")

    except subprocess.CalledProcessError as e:
        _LOGGER.error(f"💥 Database dump failed: {e}")
        if e.stderr:
            _LOGGER.error(f"stderr: {e.stderr}")
        if dump_file.exists():
            dump_file.unlink()
        raise e

    except Exception as e:
        _LOGGER.error(f"⚠️ Unexpected error during database dump: {e}")
        if dump_file.exists():
            dump_file.unlink()
        raise e
