"""Parsing module - sheet detection, header finding, column mapping."""

from autoconvert.parsing.column_mapper import map_columns, map_columns_with_subheader
from autoconvert.parsing.header_finder import find_header_row
from autoconvert.parsing.merged_cells import MergeTracker
from autoconvert.parsing.sheet_detector import detect_sheets

__all__ = [
    "detect_sheets",
    "find_header_row",
    "map_columns",
    "map_columns_with_subheader",
    "MergeTracker",
]
