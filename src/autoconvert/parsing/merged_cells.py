"""Merged cell tracking and handling.

This module provides MergeTracker for capturing merge ranges before unmerging,
and utilities for propagating values in string fields.
"""

from dataclasses import dataclass, field
from typing import Any

from openpyxl.worksheet.worksheet import Worksheet

from autoconvert.logging.messages import log_debug


@dataclass
class MergeRange:
    """A single merged cell range.

    Attributes:
        min_row: First row (1-based).
        max_row: Last row (1-based).
        min_col: First column (1-based).
        max_col: Last column (1-based).
    """

    min_row: int
    max_row: int
    min_col: int
    max_col: int

    def contains(self, row: int, col: int) -> bool:
        """Check if a cell is within this merge range.

        Args:
            row (int): 1-based row number.
            col (int): 1-based column number.

        Returns:
            bool: True if cell is in this range.
        """
        return (
            self.min_row <= row <= self.max_row and self.min_col <= col <= self.max_col
        )

    def is_origin(self, row: int, col: int) -> bool:
        """Check if a cell is the origin (top-left) of this merge.

        Args:
            row (int): 1-based row number.
            col (int): 1-based column number.

        Returns:
            bool: True if cell is the origin.
        """
        return row == self.min_row and col == self.min_col

    @property
    def is_vertical(self) -> bool:
        """Check if this is a vertical merge (same column, multiple rows)."""
        return self.min_col == self.max_col and self.min_row < self.max_row

    @property
    def is_horizontal(self) -> bool:
        """Check if this is a horizontal merge (same row, multiple columns)."""
        return self.min_row == self.max_row and self.min_col < self.max_col


@dataclass
class MergeTracker:
    """Tracks merged cell ranges for a worksheet.

    Captures merge info BEFORE unmerging, then provides utilities for:
    - Finding merge origin for any cell
    - Checking if cell is first row of merge
    - Filtering merges by column
    """

    merges: list[MergeRange] = field(default_factory=list)
    _origin_map: dict[tuple[int, int], tuple[int, int]] = field(default_factory=dict)

    @classmethod
    def from_sheet(cls, sheet: Worksheet) -> "MergeTracker":
        """Create tracker and capture all merge ranges from sheet.

        Args:
            sheet (Worksheet): The worksheet to capture merges from.

        Returns:
            MergeTracker: Tracker with all merges captured.
        """
        tracker = cls()

        # Capture all merged cell ranges
        for merge_range in list(sheet.merged_cells.ranges):
            mr = MergeRange(
                min_row=merge_range.min_row,
                max_row=merge_range.max_row,
                min_col=merge_range.min_col,
                max_col=merge_range.max_col,
            )
            tracker.merges.append(mr)

            # Build origin map for quick lookup
            for row in range(mr.min_row, mr.max_row + 1):
                for col in range(mr.min_col, mr.max_col + 1):
                    tracker._origin_map[(row, col)] = (mr.min_row, mr.min_col)

        return tracker

    def get_origin(self, row: int, col: int) -> tuple[int, int] | None:
        """Get the origin cell for a merged range containing this cell.

        Args:
            row (int): 1-based row number.
            col (int): 1-based column number.

        Returns:
            tuple[int, int] | None: (origin_row, origin_col) or None if not merged.
        """
        return self._origin_map.get((row, col))

    def is_first_row_of_merge(self, row: int, col: int) -> bool:
        """Check if this cell is in the first row of its merged range.

        Args:
            row (int): 1-based row number.
            col (int): 1-based column number.

        Returns:
            bool: True if first row of merge, or cell is not merged.
        """
        origin = self.get_origin(row, col)
        if origin is None:
            return True  # Not merged, treat as first row
        return row == origin[0]

    def is_merged(self, row: int, col: int) -> bool:
        """Check if a cell is part of a merged range.

        Args:
            row (int): 1-based row number.
            col (int): 1-based column number.

        Returns:
            bool: True if cell is part of a merge.
        """
        return (row, col) in self._origin_map

    def get_merge_for_cell(self, row: int, col: int) -> MergeRange | None:
        """Get the merge range containing a cell.

        Args:
            row (int): 1-based row number.
            col (int): 1-based column number.

        Returns:
            MergeRange | None: The merge range, or None if not merged.
        """
        for merge in self.merges:
            if merge.contains(row, col):
                return merge
        return None

    def get_merges_for_column(self, col: int) -> list[MergeRange]:
        """Get all merges that include a specific column.

        Args:
            col (int): 1-based column number.

        Returns:
            list[MergeRange]: Merges involving this column.
        """
        return [m for m in self.merges if m.min_col <= col <= m.max_col]


def unmerge_all(sheet: Worksheet) -> None:
    """Unmerge all merged cells in a worksheet.

    After unmerging, only the top-left cell retains the value.
    Other cells in the merge will be empty.

    Args:
        sheet (Worksheet): The worksheet to unmerge.
    """
    # Make a copy of merge ranges since we're modifying during iteration
    merge_ranges = list(sheet.merged_cells.ranges)

    for merge_range in merge_ranges:
        sheet.unmerge_cells(str(merge_range))


def propagate_string_values(
    sheet: Worksheet,
    tracker: MergeTracker,
    column_indices: list[int],
    header_row: int,
) -> None:
    """Propagate string values from merge origins to all cells in merge.

    Only propagates for merges that START after the header row (data merges).
    Header merges (starting at or before header_row) are not propagated.

    Args:
        sheet (Worksheet): The worksheet (after unmerging).
        tracker (MergeTracker): Merge tracker with original merge info.
        column_indices (list[int]): 1-based column indices to propagate.
        header_row (int): 1-based header row number.
    """
    for merge in tracker.merges:
        # Skip header merges (starts at or before header row)
        if merge.min_row <= header_row:
            continue

        # Check if merge involves any of the target columns
        for col in column_indices:
            if merge.min_col <= col <= merge.max_col:
                # Get origin value
                origin_value = sheet.cell(row=merge.min_row, column=col).value

                if origin_value is not None:
                    # Propagate to all cells in merge
                    for row in range(merge.min_row, merge.max_row + 1):
                        if row != merge.min_row:  # Skip origin cell
                            sheet.cell(row=row, column=col).value = origin_value
