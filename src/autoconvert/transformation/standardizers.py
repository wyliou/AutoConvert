"""Code standardization using lookup tables."""

import re

from autoconvert.core.errors import WarningCode
from autoconvert.core.models import InvoiceItem, ValidationResult

# Placeholder values to treat as empty
PLACEHOLDER_VALUES = {
    "*",
    "**",
    "***",
    "****",
    "/",
    "//",
    "-",
    "--",
    "N/A",
    "NA",
    "NONE",
    "NULL",
}


def standardize_currency(
    value: str,
    currency_rules: dict[str, str],
    validation: ValidationResult,
) -> str:
    """Standardize currency value using lookup table.

    Args:
        value (str): Raw currency value.
        currency_rules (dict[str, str]): Currency lookup table.
        validation (ValidationResult): For recording warnings.

    Returns:
        str: Standardized currency code, or original if not found.
    """
    if not value:
        return ""

    # Normalize: uppercase, trimmed
    normalized = value.strip().upper()

    # Try direct lookup
    if normalized in currency_rules:
        return currency_rules[normalized]

    # Try with whitespace removed
    no_space = normalized.replace(" ", "")
    if no_space in currency_rules:
        return currency_rules[no_space]

    # Not found - add warning
    validation.add_warning(
        WarningCode.UNSTANDARDIZED_CURRENCY,
        f"Unstandardized currency: {value}",
    )

    return value


def standardize_country(
    value: str,
    country_rules: dict[str, str],
    validation: ValidationResult,
) -> str:
    """Standardize country/COO value using lookup table.

    Args:
        value (str): Raw country value.
        country_rules (dict[str, str]): Country lookup table.
        validation (ValidationResult): For recording warnings.

    Returns:
        str: Standardized country code, or original if not found.
    """
    if not value:
        return ""

    # Check for placeholder values
    if value.strip().upper() in PLACEHOLDER_VALUES:
        return ""

    # Normalize: uppercase, trimmed
    normalized = value.strip().upper()

    # Try direct lookup
    if normalized in country_rules:
        return country_rules[normalized]

    # Try with ALL whitespace removed (e.g., "MADE IN CHINA" -> "MADEINCHINA")
    no_space = re.sub(r"\s+", "", normalized)
    if no_space in country_rules:
        return country_rules[no_space]

    # Not found - add warning
    validation.add_warning(
        WarningCode.UNSTANDARDIZED_COO,
        f"Unstandardized COO: {value}",
    )

    return value


def apply_cod_override(item: InvoiceItem) -> str:
    """Apply COD override to COO if COD has a valid value.

    Per FR28: When COD exists and is non-empty, use it instead of COO.

    Args:
        item (InvoiceItem): The invoice item.

    Returns:
        str: COO value to use (either original COO or COD override).
    """
    cod = item.cod.strip().upper() if item.cod else ""

    # Check if COD is a placeholder
    if cod and cod not in PLACEHOLDER_VALUES:
        return item.cod.strip()

    return item.coo.strip()


def standardize_codes(
    items: list[InvoiceItem],
    currency_rules: dict[str, str],
    country_rules: dict[str, str],
    validation: ValidationResult,
) -> None:
    """Standardize currency and country codes for all items.

    Modifies items in-place.

    Args:
        items (list[InvoiceItem]): Invoice items to standardize.
        currency_rules (dict[str, str]): Currency lookup table.
        country_rules (dict[str, str]): Country lookup table.
        validation (ValidationResult): For recording warnings.
    """
    # Track which codes have already been warned about
    warned_currencies: set[str] = set()
    warned_countries: set[str] = set()

    for item in items:
        # Apply COD override first
        coo_to_use = apply_cod_override(item)

        # Standardize currency
        original_currency = item.currency
        if original_currency and original_currency.upper() not in warned_currencies:
            # Create temporary validation to check if warning needed
            temp_validation = ValidationResult()
            item.currency = standardize_currency(
                original_currency, currency_rules, temp_validation
            )

            # If warning was added, add to main validation (once per unique value)
            if temp_validation.has_warnings():
                validation.warnings.extend(temp_validation.warnings)
                warned_currencies.add(original_currency.upper())
        elif original_currency:
            # Already warned, just standardize silently
            temp_validation = ValidationResult()
            item.currency = standardize_currency(
                original_currency, currency_rules, temp_validation
            )

        # Standardize country
        original_coo = coo_to_use
        if original_coo and original_coo.upper() not in warned_countries:
            temp_validation = ValidationResult()
            item.coo = standardize_country(original_coo, country_rules, temp_validation)

            if temp_validation.has_warnings():
                validation.warnings.extend(temp_validation.warnings)
                warned_countries.add(original_coo.upper())
        elif original_coo:
            temp_validation = ValidationResult()
            item.coo = standardize_country(original_coo, country_rules, temp_validation)
