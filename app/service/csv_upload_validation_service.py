import csv
import io
from collections.abc import Generator
from contextlib import contextmanager
from typing import BinaryIO, TextIO

from enums.csv_columns import CSVColumn

EXPECTED_COLUMNS: list[str] = [col.value for col in CSVColumn]
DATA_PROVIDER_COLUMN = "data_provider"


class CSVValidationError(Exception):
    """Raised when an uploaded CSV fails validation."""


@contextmanager
def _text_reader(file: BinaryIO) -> Generator[TextIO, None, None]:
    """Read a binary upload as text without closing it afterwards."""
    file.seek(0)
    wrapper = io.TextIOWrapper(file, encoding="utf-8-sig", newline="")
    try:
        yield wrapper
    finally:
        wrapper.detach()
        file.seek(0)


def _check_columns_present(header: list[str]) -> None:
    missing = [col for col in EXPECTED_COLUMNS if col not in header]
    if missing:
        raise CSVValidationError(f"Missing required columns: {', '.join(missing)}")


def _check_column_order(header: list[str]) -> None:
    present = [col for col in header if col in EXPECTED_COLUMNS]
    if present != EXPECTED_COLUMNS:
        raise CSVValidationError(
            f"Columns are in the wrong order. Expected: {', '.join(EXPECTED_COLUMNS)}"
        )


def _check_data_provider(header: list[str], first_row: list[str] | None) -> None:
    if first_row is None:
        raise CSVValidationError("The file has a header row but no data rows.")

    index = header.index(DATA_PROVIDER_COLUMN)
    value = first_row[index].strip() if index < len(first_row) else ""
    if not value:
        raise CSVValidationError(
            f"'{DATA_PROVIDER_COLUMN}' must not be empty in the first row."
        )


def validate_csv(file: BinaryIO) -> None:
    """
    Validate an uploaded CSV, raising CSVValidationError on the first failure.

    Checks, in order: all headers present, headers in the right order,
    and data_provider populated in the first data row.
    """
    try:
        with _text_reader(file) as text:
            reader = csv.reader(text)
            header = [h.strip() for h in next(reader, [])]
            first_row = next(reader, None)
    except (UnicodeDecodeError, csv.Error) as e:
        raise CSVValidationError("The file could not be read as a UTF-8 CSV.") from e

    if not header:
        raise CSVValidationError("The file is empty.")

    _check_columns_present(header)
    _check_column_order(header)
    _check_data_provider(header, first_row)
