"""Atomic file writing for output files."""

import tempfile
from pathlib import Path

from openpyxl import Workbook

from autoconvert.core.errors import ErrorCode
from autoconvert.core.models import ValidationResult
from autoconvert.logging.messages import log_output_written


def write_output(
    workbook: Workbook,
    output_folder: Path,
    input_filename: str,
    validation: ValidationResult,
) -> Path | None:
    """Write output file with atomic write pattern.

    Uses temp file + rename for safety. Sanitizes filename.

    Args:
        workbook (Workbook): Populated workbook.
        output_folder (Path): Output folder path.
        input_filename (str): Original input filename (without extension).
        validation (ValidationResult): For recording errors.

    Returns:
        Path | None: Output file path, or None if failed.
    """
    # Sanitize filename
    safe_name = _sanitize_filename(input_filename)
    output_name = f"{safe_name}_template.xlsx"
    output_path = output_folder / output_name

    try:
        # Ensure output folder exists
        output_folder.mkdir(parents=True, exist_ok=True)

        # Write to temp file first
        temp_fd, temp_path = tempfile.mkstemp(suffix=".xlsx", dir=output_folder)

        try:
            # Close the file descriptor immediately - workbook.save will open the file
            import os
            os.close(temp_fd)

            workbook.save(temp_path)

            # Atomic rename
            temp_file = Path(temp_path)

            # Remove existing file if present
            if output_path.exists():
                output_path.unlink()

            temp_file.rename(output_path)

            log_output_written(output_path)
            return output_path

        except Exception as e:
            # Clean up temp file on error
            try:
                Path(temp_path).unlink()
            except Exception:
                pass
            raise e

    except Exception as e:
        validation.add_error(
            ErrorCode.OUTPUT_WRITE_FAILED,
            f"Failed to write output file: {e}",
        )
        return None


def _sanitize_filename(filename: str) -> str:
    """Sanitize filename by replacing invalid characters.

    Args:
        filename (str): Original filename.

    Returns:
        str: Sanitized filename.
    """
    # Invalid filename characters
    invalid_chars = r'<>:"/\|?*'

    result = filename
    for char in invalid_chars:
        result = result.replace(char, "_")

    # Remove trailing dots and spaces
    result = result.rstrip(". ")

    return result
