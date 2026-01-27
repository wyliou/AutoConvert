"""File discovery and access checking for Excel files."""

from pathlib import Path

from autoconvert.logging.messages import log_debug


def discover_files(data_folder: Path) -> list[Path]:
    """Discover Excel files in the data folder.

    Args:
        data_folder (Path): Path to the data folder.

    Returns:
        list[Path]: List of Excel file paths (.xls and .xlsx).
    """
    if not data_folder.exists():
        return []

    excel_files = []

    for file_path in data_folder.iterdir():
        if file_path.is_file():
            ext = file_path.suffix.lower()
            if ext in (".xls", ".xlsx"):
                # Skip temporary/lock files
                if file_path.name.startswith("~$"):
                    continue
                excel_files.append(file_path)

    # Sort by name for consistent processing order
    excel_files.sort(key=lambda p: p.name.lower())

    return excel_files


def is_file_locked(file_path: Path) -> bool:
    """Check if a file is locked by another process.

    Args:
        file_path (Path): Path to the file.

    Returns:
        bool: True if file is locked, False if accessible.
    """
    try:
        # Try to open file in exclusive mode
        with open(file_path, "rb") as f:
            # Try to read a small portion
            f.read(1)
        return False
    except PermissionError:
        log_debug(f"File locked: {file_path}")
        return True
    except IOError:
        log_debug(f"IO error checking file lock: {file_path}")
        return True


def get_file_size(file_path: Path) -> int:
    """Get file size in bytes.

    Args:
        file_path (Path): Path to the file.

    Returns:
        int: File size in bytes, or 0 if error.
    """
    try:
        return file_path.stat().st_size
    except Exception:
        return 0
