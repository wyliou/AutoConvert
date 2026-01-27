"""Workbook loading abstraction."""

from pathlib import Path

from openpyxl import Workbook, load_workbook

from autoconvert.core.errors import ErrorCode
from autoconvert.core.models import ValidationResult
from autoconvert.ingestion.converter import convert_xls_to_workbook
from autoconvert.ingestion.discovery import is_file_locked


def open_workbook(file_path: Path, validation: ValidationResult) -> Workbook | None:
    """Open an Excel file as openpyxl Workbook.

    Handles both .xls and .xlsx formats. For .xls files, converts to
    openpyxl workbook in-memory using xlrd.

    Args:
        file_path (Path): Path to Excel file.
        validation (ValidationResult): Validation result to record errors.

    Returns:
        Workbook | None: openpyxl Workbook, or None if failed.
    """
    # Check if file is locked
    if is_file_locked(file_path):
        validation.add_error(
            ErrorCode.FILE_LOCKED,
            f"File is locked (open in Excel?): {file_path.name}",
        )
        return None

    ext = file_path.suffix.lower()

    try:
        if ext == ".xls":
            # Convert legacy format
            return convert_xls_to_workbook(file_path)
        else:
            # Load xlsx directly with data_only=True to get calculated formula values
            return load_workbook(file_path, data_only=True)

    except Exception as e:
        validation.add_error(
            ErrorCode.FILE_CORRUPTED,
            f"Cannot read Excel file: {file_path.name} - {e}",
        )
        return None
