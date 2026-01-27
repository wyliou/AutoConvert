"""Integration tests for extraction/invoice.py."""

import pytest

from autoconvert.core.models import ColumnMap, ValidationResult
from autoconvert.extraction.invoice import (
    STOP_KEYWORDS,
    extract_invoice_items,
)
from autoconvert.parsing.merged_cells import MergeTracker
from autoconvert.setup.registry import PatternRegistry


class TestExtractInvoiceItems:
    """Tests for extract_invoice_items function."""

    def test_extracts_basic_items(
        self,
        mock_worksheet,
        minimal_registry: PatternRegistry,
        validation_result: ValidationResult,
    ):
        """Test basic item extraction from invoice sheet."""
        # Setup: header at row 7, data starting at row 8
        data = [
            [""] * 10,  # Row 1
            [""] * 10,  # Row 2
            [""] * 10,  # Row 3
            [""] * 10,  # Row 4
            [""] * 10,  # Row 5
            [""] * 10,  # Row 6
            # Row 7: Headers
            ["Part No", "PO No", "Qty", "Price", "Amount", "Currency", "COO", "Brand", "Type", "Model"],
            # Row 8: Data row 1
            ["ABC-001", "PO12345", 100, 1.50, 150.00, "USD", "CN", "BrandA", "OEM", "ModelX"],
            # Row 9: Data row 2
            ["DEF-002", "PO67890", 200, 2.00, 400.00, "USD", "TW", "BrandB", "OEM", "ModelY"],
        ]
        sheet = mock_worksheet(data)

        column_map = ColumnMap(
            columns={
                "part_no": 0,
                "po_no": 1,
                "qty": 2,
                "price": 3,
                "amount": 4,
                "currency": 5,
                "coo": 6,
                "brand": 7,
                "brand_type": 8,
                "model": 9,
            },
            header_row=7,
            has_subheader=False,
        )
        tracker = MergeTracker()

        items = extract_invoice_items(
            sheet, column_map, tracker, minimal_registry, validation_result
        )

        assert len(items) == 2
        assert items[0].part_no == "ABC-001"
        assert items[0].po_no == "PO12345"
        assert items[0].qty == 100.0
        assert items[0].currency == "USD"
        assert items[1].part_no == "DEF-002"

    def test_stops_at_total_keyword(
        self,
        mock_worksheet,
        minimal_registry: PatternRegistry,
        validation_result: ValidationResult,
    ):
        """Test extraction stops at 'Total' row."""
        data = [
            [""] * 10,
            [""] * 10,
            [""] * 10,
            [""] * 10,
            [""] * 10,
            [""] * 10,
            ["Part No", "PO No", "Qty", "Price", "Amount", "Currency", "COO", "Brand", "Type", "Model"],
            # Row 8: Data
            ["ABC-001", "PO001", 100, 1.00, 100.00, "USD", "CN", "Brand", "OEM", "M1"],
            # Row 9: Total row - should stop here
            ["Total", "", 100, "", 100.00, "", "", "", "", ""],
            # Row 10: Should not be extracted
            ["XYZ-999", "PO999", 999, 9.99, 999.00, "USD", "JP", "Brand", "OEM", "M9"],
        ]
        sheet = mock_worksheet(data)

        column_map = ColumnMap(
            columns={
                "part_no": 0,
                "po_no": 1,
                "qty": 2,
                "price": 3,
                "amount": 4,
                "currency": 5,
                "coo": 6,
                "brand": 7,
                "brand_type": 8,
                "model": 9,
            },
            header_row=7,
        )
        tracker = MergeTracker()

        items = extract_invoice_items(
            sheet, column_map, tracker, minimal_registry, validation_result
        )

        # Should only get 1 item (before Total row)
        assert len(items) == 1
        assert items[0].part_no == "ABC-001"

    def test_stops_at_blank_row(
        self,
        mock_worksheet,
        minimal_registry: PatternRegistry,
        validation_result: ValidationResult,
    ):
        """Test extraction stops at blank row after data."""
        data = [
            [""] * 10,
            [""] * 10,
            [""] * 10,
            [""] * 10,
            [""] * 10,
            [""] * 10,
            ["Part No", "PO No", "Qty", "Price", "Amount", "Currency", "COO", "Brand", "Type", "Model"],
            # Row 8: Data
            ["ABC-001", "PO001", 100, 1.00, 100.00, "USD", "CN", "Brand", "OEM", "M1"],
            # Row 9: Blank row - should stop here
            [None, None, None, None, None, None, None, None, None, None],
            # Row 10: Should not be extracted
            ["XYZ-999", "PO999", 999, 9.99, 999.00, "USD", "JP", "Brand", "OEM", "M9"],
        ]
        sheet = mock_worksheet(data)

        column_map = ColumnMap(
            columns={
                "part_no": 0,
                "po_no": 1,
                "qty": 2,
                "price": 3,
                "amount": 4,
                "currency": 5,
                "coo": 6,
                "brand": 7,
                "brand_type": 8,
                "model": 9,
            },
            header_row=7,
        )
        tracker = MergeTracker()

        items = extract_invoice_items(
            sheet, column_map, tracker, minimal_registry, validation_result
        )

        assert len(items) == 1

    def test_handles_numeric_conversion(
        self,
        mock_worksheet,
        minimal_registry: PatternRegistry,
        validation_result: ValidationResult,
    ):
        """Test numeric values are properly converted."""
        data = [
            [""] * 10,
            [""] * 10,
            [""] * 10,
            [""] * 10,
            [""] * 10,
            [""] * 10,
            ["Part No", "PO No", "Qty", "Price", "Amount", "Currency", "COO", "Brand", "Type", "Model"],
            # Row 8: Data with various numeric formats
            ["ABC-001", "PO001", "100", "1.50", 150.00, "USD", "CN", "Brand", "OEM", "M1"],
        ]
        sheet = mock_worksheet(data)

        column_map = ColumnMap(
            columns={
                "part_no": 0,
                "po_no": 1,
                "qty": 2,
                "price": 3,
                "amount": 4,
                "currency": 5,
                "coo": 6,
                "brand": 7,
                "brand_type": 8,
                "model": 9,
            },
            header_row=7,
        )
        tracker = MergeTracker()

        items = extract_invoice_items(
            sheet, column_map, tracker, minimal_registry, validation_result
        )

        assert len(items) == 1
        assert items[0].qty == 100.0
        assert items[0].price == 1.50


class TestStopKeywords:
    """Tests for STOP_KEYWORDS constant."""

    def test_contains_total(self):
        """Test 'total' is a stop keyword."""
        assert "total" in STOP_KEYWORDS

    def test_contains_chinese_keywords(self):
        """Test Chinese total keywords are included."""
        assert "合计" in STOP_KEYWORDS
        assert "总计" in STOP_KEYWORDS
