"""Ingestion module - file discovery and workbook loading."""

from autoconvert.ingestion.discovery import discover_files
from autoconvert.ingestion.workbook import open_workbook

__all__ = [
    "discover_files",
    "open_workbook",
]
