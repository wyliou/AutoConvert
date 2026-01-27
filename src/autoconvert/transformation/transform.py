"""Main transformation orchestration."""

from autoconvert.core.models import InvoiceItem, ValidationResult
from autoconvert.transformation.cleaners import clean_po_number
from autoconvert.transformation.standardizers import standardize_codes


def transform_items(
    items: list[InvoiceItem],
    header_inv_no: str | None,
    currency_rules: dict[str, str],
    country_rules: dict[str, str],
    validation: ValidationResult,
) -> list[InvoiceItem]:
    """Transform invoice items: clean and standardize values.

    Performs:
    - PO number cleaning (FR26)
    - Invoice number fallback from header (FR16)
    - Currency/country code standardization (FR28)

    Args:
        items (list[InvoiceItem]): Invoice items to transform.
        header_inv_no (str | None): Invoice number from header extraction.
        currency_rules (dict[str, str]): Currency lookup table.
        country_rules (dict[str, str]): Country lookup table.
        validation (ValidationResult): For recording warnings.

    Returns:
        list[InvoiceItem]: Transformed items (modified in-place).
    """
    for item in items:
        # Clean PO number (FR26)
        item.po_no = clean_po_number(item.po_no)

        # Apply header inv_no fallback (FR16)
        # Per-row inv_no takes precedence
        if not item.inv_no and header_inv_no:
            item.inv_no = header_inv_no

    # Standardize currency and country codes (FR28)
    standardize_codes(items, currency_rules, country_rules, validation)

    return items
