"""Unit tests for validation/rules.py and validation/classifier.py."""

import math

import pytest

from autoconvert.core.models import ValidationResult
from autoconvert.validation.classifier import classify_status
from autoconvert.validation.rules import (
    REQUIRED_INVOICE_FIELDS,
    _is_empty_string,
    validate_invoice_items,
    validate_required_fields,
)


class TestIsEmptyString:
    """Tests for _is_empty_string helper function."""

    def test_none_is_empty(self):
        """Test None returns True."""
        assert _is_empty_string(None) is True

    def test_empty_string_is_empty(self):
        """Test empty string returns True."""
        assert _is_empty_string("") is True

    def test_whitespace_is_empty(self):
        """Test whitespace-only string returns True."""
        assert _is_empty_string("   ") is True
        assert _is_empty_string("\t\n") is True

    def test_non_empty_string_is_not_empty(self):
        """Test non-empty string returns False."""
        assert _is_empty_string("hello") is False
        assert _is_empty_string("  hello  ") is False

    def test_number_is_not_empty(self):
        """Test number is not considered empty."""
        assert _is_empty_string(123) is False
        assert _is_empty_string(0) is False


class TestValidateRequiredFields:
    """Tests for validate_required_fields function."""

    def test_all_fields_valid(self, make_invoice_item, validation_result: ValidationResult):
        """Test validation passes with all required fields present."""
        items = [make_invoice_item()]

        result = validate_required_fields(items, validation_result)

        assert result is True
        assert not validation_result.has_errors()

    def test_empty_part_no_fails(self, make_invoice_item, validation_result: ValidationResult):
        """Test empty part_no causes error."""
        items = [make_invoice_item(part_no="")]

        result = validate_required_fields(items, validation_result)

        assert result is False
        assert validation_result.has_errors()
        assert "ERR_030" in validation_result.errors[0][0]
        assert "part_no" in validation_result.errors[0][1]

    def test_empty_currency_fails(self, make_invoice_item, validation_result: ValidationResult):
        """Test empty currency causes error."""
        items = [make_invoice_item(currency="")]

        result = validate_required_fields(items, validation_result)

        assert result is False
        assert "currency" in validation_result.errors[0][1]

    def test_whitespace_only_field_fails(
        self, make_invoice_item, validation_result: ValidationResult
    ):
        """Test whitespace-only field causes error."""
        items = [make_invoice_item(brand="   ")]

        result = validate_required_fields(items, validation_result)

        assert result is False
        assert "brand" in validation_result.errors[0][1]

    def test_nan_numeric_fails(self, make_invoice_item, validation_result: ValidationResult):
        """Test NaN numeric value causes error."""
        items = [make_invoice_item(qty=float("nan"))]

        result = validate_required_fields(items, validation_result)

        assert result is False
        assert "ERR_031" in validation_result.errors[0][0]
        assert "qty" in validation_result.errors[0][1]

    def test_inf_numeric_fails(self, make_invoice_item, validation_result: ValidationResult):
        """Test Inf numeric value causes error."""
        items = [make_invoice_item(price=float("inf"))]

        result = validate_required_fields(items, validation_result)

        assert result is False
        assert "price" in validation_result.errors[0][1]

    def test_zero_numeric_passes(self, make_invoice_item, validation_result: ValidationResult):
        """Test zero numeric values are allowed."""
        items = [make_invoice_item(qty=0.0, price=0.0, amount=0.0)]

        result = validate_required_fields(items, validation_result)

        assert result is True
        assert not validation_result.has_errors()

    def test_multiple_errors_collected(
        self, make_invoice_item, validation_result: ValidationResult
    ):
        """Test all errors are collected, not just first."""
        items = [make_invoice_item(part_no="", po_no="", currency="")]

        validate_required_fields(items, validation_result)

        assert len(validation_result.errors) == 3

    def test_multiple_items_validated(
        self, make_invoice_item, validation_result: ValidationResult
    ):
        """Test all items in list are validated."""
        items = [
            make_invoice_item(row=1),
            make_invoice_item(row=2, part_no=""),
        ]

        result = validate_required_fields(items, validation_result)

        assert result is False
        assert "row 2" in validation_result.errors[0][1]


class TestValidateInvoiceItems:
    """Tests for validate_invoice_items function."""

    def test_delegates_to_validate_required_fields(
        self, make_invoice_item, validation_result: ValidationResult
    ):
        """Test validate_invoice_items calls validate_required_fields."""
        items = [make_invoice_item()]

        result = validate_invoice_items(items, validation_result)

        assert result is True


class TestClassifyStatus:
    """Tests for classify_status function."""

    def test_no_errors_no_warnings_is_success(self):
        """Test empty validation result yields SUCCESS."""
        validation = ValidationResult()

        assert classify_status(validation) == "SUCCESS"

    def test_errors_yields_failed(self):
        """Test any error yields FAILED."""
        validation = ValidationResult()
        validation.add_error("ERR_001", "Error", log=False)

        assert classify_status(validation) == "FAILED"

    def test_warnings_only_yields_attention(self):
        """Test warnings without errors yields ATTENTION."""
        validation = ValidationResult()
        validation.add_warning("ATT_001", "Warning", log=False)

        assert classify_status(validation) == "ATTENTION"

    def test_errors_and_warnings_yields_failed(self):
        """Test errors take precedence over warnings."""
        validation = ValidationResult()
        validation.add_error("ERR_001", "Error", log=False)
        validation.add_warning("ATT_001", "Warning", log=False)

        assert classify_status(validation) == "FAILED"

    def test_multiple_warnings_yields_attention(self):
        """Test multiple warnings still yields ATTENTION."""
        validation = ValidationResult()
        validation.add_warning("ATT_001", "Warning 1", log=False)
        validation.add_warning("ATT_002", "Warning 2", log=False)

        assert classify_status(validation) == "ATTENTION"


class TestRequiredInvoiceFields:
    """Tests for REQUIRED_INVOICE_FIELDS constant."""

    def test_contains_expected_fields(self):
        """Test all expected required fields are present."""
        expected = [
            "part_no",
            "po_no",
            "qty",
            "price",
            "amount",
            "currency",
            "coo",
            "brand",
            "brand_type",
            "model",
        ]

        for field in expected:
            assert field in REQUIRED_INVOICE_FIELDS

    def test_does_not_contain_optional_fields(self):
        """Test optional fields are not in required list."""
        optional = ["serial", "inv_no", "cod", "weight"]

        for field in optional:
            assert field not in REQUIRED_INVOICE_FIELDS
