"""Unit tests for transformation/standardizers.py."""

import pytest

from autoconvert.core.models import ValidationResult
from autoconvert.transformation.standardizers import (
    PLACEHOLDER_VALUES,
    apply_cod_override,
    standardize_country,
    standardize_currency,
)


class TestStandardizeCurrency:
    """Tests for standardize_currency function."""

    def test_direct_lookup_hit(self, currency_rules: dict[str, str]):
        """Test direct lookup succeeds."""
        validation = ValidationResult()
        result = standardize_currency("USD", currency_rules, validation)

        assert result == "USD"
        assert not validation.has_warnings()

    def test_lookup_with_normalization(self, currency_rules: dict[str, str]):
        """Test lookup after uppercase normalization."""
        validation = ValidationResult()
        result = standardize_currency("usd", currency_rules, validation)

        assert result == "USD"
        assert not validation.has_warnings()

    def test_lookup_with_whitespace(self, currency_rules: dict[str, str]):
        """Test lookup handles extra whitespace."""
        validation = ValidationResult()
        result = standardize_currency("  USD  ", currency_rules, validation)

        assert result == "USD"
        assert not validation.has_warnings()

    def test_name_to_code_lookup(self, currency_rules: dict[str, str]):
        """Test currency name maps to code."""
        validation = ValidationResult()
        result = standardize_currency("US DOLLAR", currency_rules, validation)

        assert result == "USD"

    def test_unknown_currency_returns_original_with_warning(
        self, currency_rules: dict[str, str]
    ):
        """Test unknown currency returns original and adds warning."""
        validation = ValidationResult()
        result = standardize_currency("UNKNOWN", currency_rules, validation)

        assert result == "UNKNOWN"
        assert validation.has_warnings()
        assert "ATT_003" in validation.warnings[0][0]

    def test_empty_string_returns_empty(self, currency_rules: dict[str, str]):
        """Test empty input returns empty without warning."""
        validation = ValidationResult()
        result = standardize_currency("", currency_rules, validation)

        assert result == ""
        assert not validation.has_warnings()

    def test_whitespace_only_returns_with_warning(self, currency_rules: dict[str, str]):
        """Test whitespace-only input returns original with warning (not in lookup).

        The function doesn't treat whitespace as empty - it passes through the
        normalization and lookup logic, ultimately returning the original value
        with a warning since whitespace-only strings aren't in the lookup table.
        """
        validation = ValidationResult()
        result = standardize_currency("   ", currency_rules, validation)

        # Whitespace is truthy, so it passes the `if not value` check
        # Then normalized to "" which isn't in lookup, so warning is added
        assert result == "   "  # Original value returned
        assert validation.has_warnings()


class TestStandardizeCountry:
    """Tests for standardize_country function."""

    def test_direct_lookup(self, country_rules: dict[str, str]):
        """Test direct country code lookup."""
        validation = ValidationResult()
        result = standardize_country("CN", country_rules, validation)

        assert result == "CN"
        assert not validation.has_warnings()

    def test_full_name_lookup(self, country_rules: dict[str, str]):
        """Test full country name lookup."""
        validation = ValidationResult()
        result = standardize_country("CHINA", country_rules, validation)

        assert result == "CN"

    def test_made_in_pattern(self, country_rules: dict[str, str]):
        """Test 'MADE IN CHINA' pattern with whitespace removed."""
        validation = ValidationResult()
        result = standardize_country("MADE IN CHINA", country_rules, validation)

        assert result == "CN"

    def test_case_insensitive(self, country_rules: dict[str, str]):
        """Test case-insensitive lookup."""
        validation = ValidationResult()

        assert standardize_country("china", country_rules, validation) == "CN"
        assert standardize_country("Japan", country_rules, validation) == "JP"

    @pytest.mark.parametrize("placeholder", list(PLACEHOLDER_VALUES)[:6])
    def test_placeholder_values_return_empty(
        self, placeholder: str, country_rules: dict[str, str]
    ):
        """Test that placeholder values return empty string."""
        validation = ValidationResult()
        result = standardize_country(placeholder, country_rules, validation)

        assert result == ""
        assert not validation.has_warnings()

    def test_unknown_country_returns_original_with_warning(
        self, country_rules: dict[str, str]
    ):
        """Test unknown country returns original with warning."""
        validation = ValidationResult()
        result = standardize_country("UNKNOWN", country_rules, validation)

        assert result == "UNKNOWN"
        assert validation.has_warnings()
        assert "ATT_004" in validation.warnings[0][0]

    def test_empty_string_returns_empty(self, country_rules: dict[str, str]):
        """Test empty input returns empty without warning."""
        validation = ValidationResult()
        result = standardize_country("", country_rules, validation)

        assert result == ""
        assert not validation.has_warnings()


class TestApplyCodOverride:
    """Tests for apply_cod_override function."""

    def test_cod_overrides_coo(self, make_invoice_item):
        """Test that non-empty COD overrides COO."""
        item = make_invoice_item(coo="CN", cod="TW")
        result = apply_cod_override(item)

        assert result == "TW"

    def test_empty_cod_uses_coo(self, make_invoice_item):
        """Test that empty COD uses original COO."""
        item = make_invoice_item(coo="CN", cod="")
        result = apply_cod_override(item)

        assert result == "CN"

    @pytest.mark.parametrize("placeholder", ["N/A", "NA", "*", "-", "NONE"])
    def test_placeholder_cod_uses_coo(self, make_invoice_item, placeholder: str):
        """Test that placeholder COD uses original COO."""
        item = make_invoice_item(coo="CN", cod=placeholder)
        result = apply_cod_override(item)

        assert result == "CN"

    def test_whitespace_cod_uses_coo(self, make_invoice_item):
        """Test that whitespace-only COD uses COO."""
        item = make_invoice_item(coo="CN", cod="   ")
        result = apply_cod_override(item)

        assert result == "CN"

    def test_strips_whitespace_from_result(self, make_invoice_item):
        """Test result is stripped of whitespace."""
        item = make_invoice_item(coo="  CN  ", cod="")
        result = apply_cod_override(item)

        assert result == "CN"
