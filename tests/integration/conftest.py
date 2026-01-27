"""Fixtures specific to integration tests with mocked worksheets."""

import re
from typing import Any
from unittest.mock import MagicMock

import pytest

from autoconvert.setup.registry import FieldPattern, PatternRegistry


@pytest.fixture
def mock_worksheet():
    """Factory fixture for creating mock Worksheet objects.

    Returns a function that creates mock worksheets with specified cell data.
    """

    def _make(
        data: list[list[Any]],
        max_row: int | None = None,
        max_column: int | None = None,
    ) -> MagicMock:
        """Create a mock worksheet with specified data.

        Args:
            data: 2D list of cell values (row-major, 0-indexed internally).
                  data[0] corresponds to row 1 in worksheet.
            max_row: Override max_row property.
            max_column: Override max_column property.

        Returns:
            MagicMock: Mock worksheet object.
        """
        mock = MagicMock()

        # Set dimensions
        mock.max_row = max_row if max_row is not None else len(data)
        mock.max_column = max_column if max_column is not None else (
            max(len(row) for row in data) if data else 0
        )

        # Mock cell access - worksheet uses 1-based indexing
        def get_cell(row: int, column: int) -> MagicMock:
            cell_mock = MagicMock()
            row_idx = row - 1  # Convert 1-based to 0-based
            col_idx = column - 1

            if 0 <= row_idx < len(data) and 0 <= col_idx < len(data[row_idx]):
                cell_mock.value = data[row_idx][col_idx]
            else:
                cell_mock.value = None

            return cell_mock

        mock.cell = get_cell

        # Mock merged_cells (empty by default)
        mock.merged_cells = MagicMock()
        mock.merged_cells.ranges = []

        return mock

    return _make


@pytest.fixture
def minimal_registry() -> PatternRegistry:
    """Return a minimal PatternRegistry for testing column mapping."""
    registry = PatternRegistry()

    # Invoice sheet patterns
    registry.invoice_sheet_patterns = [
        re.compile(r"(?i)^invoice"),
        re.compile(r"(?i)^inv$"),
    ]

    # Packing sheet patterns
    registry.packing_sheet_patterns = [
        re.compile(r"(?i)^packing"),
        re.compile(r"(?i)^pack"),
    ]

    # Invoice columns - all required for invoice sheet
    registry.invoice_columns = {
        "part_no": FieldPattern(
            patterns=[re.compile(r"(?i)part\s*no"), re.compile(r"(?i)p/n")],
            field_type="string",
            required=True,
        ),
        "po_no": FieldPattern(
            patterns=[re.compile(r"(?i)po\s*no"), re.compile(r"(?i)p\.?o\.?\s*#")],
            field_type="string",
            required=True,
        ),
        "qty": FieldPattern(
            patterns=[re.compile(r"(?i)^qty"), re.compile(r"(?i)quantity")],
            field_type="numeric",
            required=True,
        ),
        "price": FieldPattern(
            patterns=[re.compile(r"(?i)price"), re.compile(r"(?i)unit\s*price")],
            field_type="numeric",
            required=True,
        ),
        "amount": FieldPattern(
            patterns=[re.compile(r"(?i)amount"), re.compile(r"(?i)total")],
            field_type="currency",
            required=True,
        ),
        "currency": FieldPattern(
            patterns=[re.compile(r"(?i)currency"), re.compile(r"(?i)curr")],
            field_type="string",
            required=True,
        ),
        "coo": FieldPattern(
            patterns=[re.compile(r"(?i)c\.?o\.?o"), re.compile(r"(?i)origin")],
            field_type="string",
            required=True,
        ),
        "brand": FieldPattern(
            patterns=[re.compile(r"(?i)brand")],
            field_type="string",
            required=True,
        ),
        "brand_type": FieldPattern(
            patterns=[re.compile(r"(?i)brand\s*type"), re.compile(r"(?i)type")],
            field_type="string",
            required=True,
        ),
        "model": FieldPattern(
            patterns=[re.compile(r"(?i)model")],
            field_type="string",
            required=True,
        ),
    }

    # Packing columns
    registry.packing_columns = {
        "part_no": FieldPattern(
            patterns=[re.compile(r"(?i)part\s*no"), re.compile(r"(?i)p/n")],
            field_type="string",
            required=True,
        ),
        "qty": FieldPattern(
            patterns=[re.compile(r"(?i)^qty"), re.compile(r"(?i)quantity")],
            field_type="numeric",
            required=True,
        ),
        "nw": FieldPattern(
            patterns=[re.compile(r"(?i)n\.?w"), re.compile(r"(?i)net\s*w")],
            field_type="numeric",
            required=True,
        ),
        "gw": FieldPattern(
            patterns=[re.compile(r"(?i)g\.?w"), re.compile(r"(?i)gross\s*w")],
            field_type="numeric",
            required=False,
        ),
        "pack": FieldPattern(
            patterns=[re.compile(r"(?i)pack"), re.compile(r"(?i)carton")],
            field_type="numeric",
            required=False,
        ),
    }

    return registry
