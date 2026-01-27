"""Integration tests for parsing/column_mapper.py."""

import pytest

from autoconvert.core.models import ValidationResult
from autoconvert.parsing.column_mapper import (
    map_columns,
    map_columns_with_subheader,
    normalize_header,
)
from autoconvert.setup.registry import PatternRegistry


class TestNormalizeHeader:
    """Tests for normalize_header function."""

    def test_collapses_whitespace(self):
        """Test multiple spaces/newlines collapsed to single space."""
        assert normalize_header("Part   No") == "Part No"
        assert normalize_header("Part\nNo") == "Part No"
        assert normalize_header("Part\t\tNo") == "Part No"
        assert normalize_header("Part\r\nNo") == "Part No"

    def test_strips_edges(self):
        """Test leading/trailing whitespace stripped."""
        assert normalize_header("  Part No  ") == "Part No"

    def test_none_returns_empty(self):
        """Test None input returns empty string."""
        assert normalize_header(None) == ""

    def test_number_converted(self):
        """Test number is converted to string."""
        assert normalize_header(123) == "123"

    def test_mixed_whitespace(self):
        """Test combination of whitespace types."""
        assert normalize_header("  Part\n  No\t  ") == "Part No"


class TestMapColumns:
    """Tests for map_columns function."""

    def test_maps_all_invoice_fields(
        self,
        mock_worksheet,
        minimal_registry: PatternRegistry,
        validation_result: ValidationResult,
    ):
        """Test successful mapping of all required invoice fields."""
        # Headers at row 7
        data = [
            [""] * 10,  # Row 1
            [""] * 10,  # Row 2
            [""] * 10,  # Row 3
            [""] * 10,  # Row 4
            [""] * 10,  # Row 5
            [""] * 10,  # Row 6
            # Row 7: Headers
            ["Part No", "PO No", "Qty", "Price", "Amount", "Currency", "COO", "Brand", "Type", "Model"],
            # Row 8: Data
            ["ABC123", "PO001", 100, 1.50, 150.00, "USD", "CN", "TestBrand", "OEM", "M1"],
        ]
        sheet = mock_worksheet(data)

        column_map = map_columns(
            sheet,
            header_row=7,
            registry=minimal_registry,
            sheet_type="invoice",
            validation=validation_result,
        )

        assert column_map is not None
        assert column_map.columns["part_no"] == 0
        assert column_map.columns["po_no"] == 1
        assert column_map.columns["qty"] == 2
        assert column_map.columns["price"] == 3
        assert column_map.columns["amount"] == 4
        assert column_map.columns["currency"] == 5
        assert column_map.columns["coo"] == 6
        assert column_map.columns["brand"] == 7
        assert column_map.columns["brand_type"] == 8
        assert column_map.columns["model"] == 9
        assert not validation_result.has_errors()

    def test_maps_packing_fields(
        self,
        mock_worksheet,
        minimal_registry: PatternRegistry,
        validation_result: ValidationResult,
    ):
        """Test mapping of packing sheet fields."""
        data = [
            [""] * 5,  # Rows 1-6 empty
            [""] * 5,
            [""] * 5,
            [""] * 5,
            [""] * 5,
            [""] * 5,
            # Row 7: Headers
            ["Part No", "Qty", "N.W.", "G.W.", "Pack"],
            # Row 8: Data
            ["ABC123", 100, 5.0, 6.0, 1],
        ]
        sheet = mock_worksheet(data)

        column_map = map_columns(
            sheet,
            header_row=7,
            registry=minimal_registry,
            sheet_type="packing",
            validation=validation_result,
        )

        assert column_map is not None
        assert column_map.columns["part_no"] == 0
        assert column_map.columns["qty"] == 1
        assert column_map.columns["nw"] == 2
        assert column_map.columns["gw"] == 3

    def test_missing_required_field_returns_none(
        self,
        mock_worksheet,
        minimal_registry: PatternRegistry,
        validation_result: ValidationResult,
    ):
        """Test that missing required field returns None with error."""
        # Missing 'amount' column
        data = [
            [""] * 10,
            [""] * 10,
            [""] * 10,
            [""] * 10,
            [""] * 10,
            [""] * 10,
            # Row 7: Headers - missing Amount
            ["Part No", "PO No", "Qty", "Price", "Currency", "COO", "Brand", "Type", "Model"],
        ]
        sheet = mock_worksheet(data)

        column_map = map_columns(
            sheet,
            header_row=7,
            registry=minimal_registry,
            sheet_type="invoice",
            validation=validation_result,
        )

        assert column_map is None
        assert validation_result.has_errors()
        assert "ERR_020" in validation_result.errors[0][0]

    def test_case_insensitive_matching(
        self,
        mock_worksheet,
        minimal_registry: PatternRegistry,
        validation_result: ValidationResult,
    ):
        """Test patterns match case-insensitively."""
        data = [
            [""] * 5,
            [""] * 5,
            [""] * 5,
            [""] * 5,
            [""] * 5,
            [""] * 5,
            ["PART NO", "QTY", "N.W.", "G.W.", "PACK"],  # All uppercase
            ["ABC", 100, 5.0, 6.0, 1],
        ]
        sheet = mock_worksheet(data)

        column_map = map_columns(
            sheet,
            header_row=7,
            registry=minimal_registry,
            sheet_type="packing",
            validation=validation_result,
        )

        assert column_map is not None
        assert "part_no" in column_map.columns

    def test_alternate_header_patterns(
        self,
        mock_worksheet,
        minimal_registry: PatternRegistry,
        validation_result: ValidationResult,
    ):
        """Test alternate header patterns are matched."""
        data = [
            [""] * 5,
            [""] * 5,
            [""] * 5,
            [""] * 5,
            [""] * 5,
            [""] * 5,
            ["P/N", "Quantity", "Net Weight", "Gross Weight"],  # Alternate patterns
            ["ABC", 100, 5.0, 6.0],
        ]
        sheet = mock_worksheet(data)

        column_map = map_columns(
            sheet,
            header_row=7,
            registry=minimal_registry,
            sheet_type="packing",
            validation=validation_result,
        )

        assert column_map is not None
        assert column_map.columns["part_no"] == 0
        assert column_map.columns["qty"] == 1
        assert column_map.columns["nw"] == 2
        assert column_map.columns["gw"] == 3

    def test_header_row_stored(
        self,
        mock_worksheet,
        minimal_registry: PatternRegistry,
        validation_result: ValidationResult,
    ):
        """Test header_row is stored in ColumnMap."""
        data = [
            [""] * 5,
            [""] * 5,
            [""] * 5,
            [""] * 5,
            [""] * 5,
            [""] * 5,
            ["Part No", "Qty", "N.W."],
        ]
        sheet = mock_worksheet(data)

        column_map = map_columns(
            sheet,
            header_row=7,
            registry=minimal_registry,
            sheet_type="packing",
            validation=validation_result,
        )

        assert column_map is not None
        assert column_map.header_row == 7


class TestMapColumnsWithSubheader:
    """Tests for map_columns_with_subheader function."""

    def test_finds_field_in_subheader(
        self,
        mock_worksheet,
        minimal_registry: PatternRegistry,
        validation_result: ValidationResult,
    ):
        """Test finding missing field in sub-header row."""
        data = [
            [""] * 5,
            [""] * 5,
            [""] * 5,
            [""] * 5,
            [""] * 5,
            [""] * 5,
            # Row 7: Main headers - NW missing from main header
            ["Part No", "Qty", "Weight", "G.W."],
            # Row 8: Sub-headers
            ["", "", "N.W.", ""],
            # Row 9: Data
            ["ABC", 100, 5.0, 6.0],
        ]
        sheet = mock_worksheet(data)

        column_map = map_columns_with_subheader(
            sheet,
            header_row=7,
            registry=minimal_registry,
            sheet_type="packing",
            validation=validation_result,
        )

        assert column_map is not None
        assert column_map.has_subheader
        assert column_map.columns["nw"] == 2

    def test_no_subheader_when_all_found(
        self,
        mock_worksheet,
        minimal_registry: PatternRegistry,
        validation_result: ValidationResult,
    ):
        """Test has_subheader is False when all fields found in main header."""
        data = [
            [""] * 5,
            [""] * 5,
            [""] * 5,
            [""] * 5,
            [""] * 5,
            [""] * 5,
            ["Part No", "Qty", "N.W.", "G.W."],
            ["ABC", 100, 5.0, 6.0],
        ]
        sheet = mock_worksheet(data)

        column_map = map_columns_with_subheader(
            sheet,
            header_row=7,
            registry=minimal_registry,
            sheet_type="packing",
            validation=validation_result,
        )

        assert column_map is not None
        assert not column_map.has_subheader

    def test_still_fails_if_field_not_in_either_row(
        self,
        mock_worksheet,
        minimal_registry: PatternRegistry,
        validation_result: ValidationResult,
    ):
        """Test returns None if required field not in header or sub-header."""
        data = [
            [""] * 5,
            [""] * 5,
            [""] * 5,
            [""] * 5,
            [""] * 5,
            [""] * 5,
            # Row 7: Missing NW entirely
            ["Part No", "Qty", "G.W."],
            # Row 8: Sub-header also missing NW
            ["", "", ""],
        ]
        sheet = mock_worksheet(data)

        column_map = map_columns_with_subheader(
            sheet,
            header_row=7,
            registry=minimal_registry,
            sheet_type="packing",
            validation=validation_result,
        )

        assert column_map is None
        assert validation_result.has_errors()
