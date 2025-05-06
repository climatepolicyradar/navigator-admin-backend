import logging
import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from app.service.database_dump import (
    delete_local_file,
    get_database_dump,
    validate_postgres_param,
)


@pytest.mark.parametrize(
    "param",
    [
        "valid_name",
        "name_with_underscore_",
        "name-with-hyphen",
        "name.with.dot",
        "numbers123",
    ],
)
def test_validate_postgres_param_valid(param):
    """Test that valid Postgres parameters pass validation"""
    assert validate_postgres_param(param) == param


@pytest.mark.parametrize(
    "param",
    [
        "invalid name",
        "invalid@name",
        "invalid/name",
        "",
        None,
    ],
)
def test_validate_postgres_param_invalid(param):
    """Test that invalid Postgres parameters raise ValueError"""
    with pytest.raises(ValueError):
        validate_postgres_param(param)


@patch("app.service.database_dump.validate_postgres_param")
@patch("app.service.database_dump.ADMIN_POSTGRES_HOST", "test-host")
@patch("app.service.database_dump.ADMIN_POSTGRES_USER", "test-user")
@patch("app.service.database_dump.ADMIN_POSTGRES_DATABASE", "test-db")
@patch("app.service.database_dump.ADMIN_POSTGRES_PASSWORD", "test-password")
@patch("app.service.database_dump.subprocess.run")
@patch("app.service.database_dump.Path")
def test_get_database_dump_success(mock_path, mock_run, mock_validate, caplog):
    """Test successful database dump"""

    # Setup mock Path object
    mock_file = MagicMock()
    mock_file.exists.return_value = False
    mock_file.__str__ = MagicMock(return_value="navigator_dump_20230101_120000.sql")
    mock_path.return_value = mock_file
    mock_validate.side_effect = ["test-host", "test-user", "test-db"]

    # Setup mock subprocess result
    mock_result = MagicMock()
    mock_result.stdout = "pg_dump output"
    mock_result.stderr = ""
    mock_run.return_value = mock_result

    # Call the function
    with caplog.at_level(logging.INFO):
        result = get_database_dump()

    assert mock_validate.call_args_list == [
        call("test-host"),
        call("test-user"),
        call("test-db"),
    ]

    assert result == "navigator_dump_20230101_120000.sql"
    mock_file.chmod.assert_called_once_with(0o600)

    # Verify command construction
    expected_cmd = [
        "pg_dump",
        "--no-password",
        "-h",
        "test-host",
        "-U",
        "test-user",
        "-d",
        "test-db",
        "-f",
        "navigator_dump_20230101_120000.sql",
        "--no-privileges",
        "--no-owner",
    ]
    mock_run.assert_called_once_with(
        expected_cmd,
        check=True,
        env={"PGPASSWORD": "test-password"},
        capture_output=True,
        text=True,
        shell=False,
        timeout=300,
    )

    assert "🚀 Starting database dump" in caplog.text
    assert "✅ Database dump completed successfully" in caplog.text


@patch("app.service.database_dump.Path")
def test_get_database_dump_raises_error_when_dump_file_exists(mock_path):
    """Test that function raises when dump file exists"""

    mock_file = MagicMock()
    mock_file.exists.return_value = True
    mock_path.return_value = mock_file

    with pytest.raises(RuntimeError, match="Dump file already exists"):
        get_database_dump()


@patch("app.service.database_dump.subprocess.run")
@patch("app.service.database_dump.Path")
def test_get_database_dump_raises_timeout_error(mock_path, mock_run, caplog):
    """Test timeout during database dump"""

    mock_file = MagicMock()
    mock_file.exists.side_effect = [False, True]  # First call: False, Second: True
    mock_file.__str__ = MagicMock(return_value="test_dump_timeout_error.sql")
    mock_path.return_value = mock_file

    mock_run.side_effect = subprocess.TimeoutExpired("pg_dump", timeout=300)

    with pytest.raises(RuntimeError, match="Database dump timed out after 5 minutes"):
        with caplog.at_level(logging.ERROR):
            get_database_dump()

    mock_file.unlink.assert_called_once()
    assert "⌛ Database dump timed out" in caplog.text


@patch("app.service.database_dump.subprocess.run")
@patch("app.service.database_dump.Path")
def test_get_database_dump_raises_process_error(mock_path, mock_run, caplog):
    """Test failed database dump"""

    mock_file = MagicMock()
    mock_file.exists.side_effect = [False, True]  # First call: False, Second: True
    mock_file.__str__ = MagicMock(return_value="test_dump_process_error.sql")
    mock_path.return_value = mock_file

    error = subprocess.CalledProcessError(
        returncode=1, cmd="pg_dump", stderr="Error: connection failed"
    )
    mock_run.side_effect = error

    with pytest.raises(subprocess.CalledProcessError):
        with caplog.at_level(logging.ERROR):
            get_database_dump()

    mock_file.unlink.assert_called_once()
    assert "💥 Database dump failed" in caplog.text
    assert "stderr: Error: connection failed" in caplog.text


@patch("app.service.database_dump.subprocess.run")
@patch("app.service.database_dump.Path")
def test_get_database_dump_raises_unexpected_error(mock_path, mock_run, caplog):
    """Test unexpected error during database dump"""

    # Setup mocks
    mock_file = MagicMock()
    mock_file.exists.side_effect = [False, True]  # First call: False, Second: True
    mock_file.__str__ = MagicMock(return_value="test_dump_for_unexpected_errors.sql")
    mock_path.return_value = mock_file

    mock_run.side_effect = Exception("Unexpected error")

    with pytest.raises(Exception, match="Unexpected error"):
        with caplog.at_level(logging.ERROR):
            get_database_dump()

    mock_file.unlink.assert_called_once()
    assert "⚠️ Unexpected error during database dump" in caplog.text


def test_delete_local_file_removes_existing_file(caplog):
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_path = tmp_file.name

    assert os.path.exists(tmp_path)
    with caplog.at_level(logging.DEBUG):
        delete_local_file(tmp_path)
    assert not os.path.exists(tmp_path)


def test_delete_local_file_handles_missing_file_gracefully(caplog):
    fake_path = str(Path(tempfile.gettempdir()) / "nonexistent_file.txt")

    if os.path.exists(fake_path):
        os.remove(fake_path)

    delete_local_file(fake_path)

    assert "Deleted local file" not in caplog.text


def test_delete_local_file_logs_and_raises_on_generic_exception(caplog):
    import logging
    from pathlib import Path

    fake_path = "/tmp/fakefile.txt"

    with (
        patch.object(Path, "exists", return_value=True),
        patch.object(Path, "unlink", side_effect=Exception("Something went wrong")),
    ):
        caplog.set_level(logging.ERROR)

        with pytest.raises(Exception, match="Something went wrong"):
            delete_local_file(fake_path)

        assert (
            f"⚠️ Failed to delete file {fake_path}: Something went wrong" in caplog.text
        )
