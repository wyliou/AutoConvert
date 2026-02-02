"""Unit tests for transformation/cleaners.py."""

import pytest

from autoconvert.transformation.cleaners import (
    clean_invoice_number,
    clean_po_number,
    strip_whitespace,
)


class TestCleanPoNumber:
    """Tests for clean_po_number function."""

    @pytest.mark.parametrize(
        "input_value,expected",
        [
            ("2250600556-2.1", "2250600556"),
            ("PO12345/1", "PO12345"),
            ("ABC123-001-A", "ABC123"),
            ("SIMPLE", "SIMPLE"),
            ("", ""),
            ("NO-SUFFIX-", "NO"),
            ("WITH/SLASH/MORE", "WITH"),
        ],
    )
    def test_removes_suffix_after_delimiter(self, input_value: str, expected: str):
        """Test that suffixes after - or / are removed."""
        assert clean_po_number(input_value) == expected

    def test_strips_whitespace(self):
        """Test that leading/trailing whitespace is stripped."""
        assert clean_po_number("  PO123-1  ") == "PO123"

    def test_empty_string_returns_empty(self):
        """Test that empty string input returns empty string."""
        assert clean_po_number("") == ""

    def test_dash_takes_precedence(self):
        """Test dash delimiter is checked before slash."""
        # Both delimiters present - dash comes first in code
        assert clean_po_number("ABC-123/456") == "ABC"

    def test_no_delimiter_returns_stripped(self):
        """Test value without delimiters returns stripped value."""
        assert clean_po_number("  SIMPLE123  ") == "SIMPLE123"


class TestCleanInvoiceNumber:
    """Tests for clean_invoice_number function."""

    @pytest.mark.parametrize(
        "input_value,expected",
        [
            ("INV#12345", "12345"),
            ("INV# 12345", "12345"),
            ("INV12345", "INV12345"),  # Bare "INV" prefix is preserved
            ("NO. ABC123", "ABC123"),
            ("NO.ABC123", "ABC123"),
            ("12345", "12345"),
            ("", ""),
        ],
    )
    def test_removes_common_prefixes(self, input_value: str, expected: str):
        """Test that INV#, NO prefixes are removed (but NOT bare INV)."""
        assert clean_invoice_number(input_value) == expected

    def test_case_insensitive(self):
        """Test that prefix matching is case-insensitive."""
        assert clean_invoice_number("inv#ABC") == "ABC"
        assert clean_invoice_number("inv#123") == "123"
        assert clean_invoice_number("no. 789") == "789"

    def test_preserves_content_without_prefix(self):
        """Test values without recognized prefixes are preserved."""
        assert clean_invoice_number("XYZ123") == "XYZ123"

    def test_strips_whitespace(self):
        """Test leading/trailing whitespace is stripped."""
        assert clean_invoice_number("  12345  ") == "12345"


class TestStripWhitespace:
    """Tests for strip_whitespace function."""

    def test_strips_string(self):
        """Test stripping a normal string."""
        assert strip_whitespace("  hello  ") == "hello"

    def test_none_returns_empty(self):
        """Test that None returns empty string."""
        assert strip_whitespace(None) == ""

    def test_number_converted_to_string(self):
        """Test that numbers are converted to string."""
        assert strip_whitespace(123) == "123"
        assert strip_whitespace(45.67) == "45.67"

    def test_empty_string_returns_empty(self):
        """Test empty string returns empty."""
        assert strip_whitespace("") == ""

    def test_whitespace_only_returns_empty(self):
        """Test whitespace-only string returns empty."""
        assert strip_whitespace("   ") == ""
        assert strip_whitespace("\t\n") == ""
