"""Core data models for AutoConvert.

Uses dataclasses for lightweight internal data structures.
Pydantic is used only at configuration boundary (setup module).
"""

from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Literal


@dataclass
class SheetInfo:
    """Information about detected invoice and packing sheets.

    Attributes:
        invoice_sheet_name: Name of the detected invoice sheet.
        packing_sheet_name: Name of the detected packing sheet.
        invoice_pattern_matched: Pattern that matched the invoice sheet.
        packing_pattern_matched: Pattern that matched the packing sheet.
    """

    invoice_sheet_name: str
    packing_sheet_name: str
    invoice_pattern_matched: str | None = None
    packing_pattern_matched: str | None = None


@dataclass
class ColumnMap:
    """Mapping of field names to column indices (0-based).

    Attributes:
        columns: Dictionary mapping field names to 0-based column indices.
        header_row: 1-based row number where headers were found.
        has_subheader: Whether a sub-header row was detected.
    """

    columns: dict[str, int] = field(default_factory=dict)
    header_row: int = 0
    has_subheader: bool = False

    def get(self, field_name: str) -> int | None:
        """Get column index for a field (0-based).

        Args:
            field_name (str): The field name to look up.

        Returns:
            int | None: 0-based column index, or None if not found.
        """
        return self.columns.get(field_name)


@dataclass
class InvoiceItem:
    """Single invoice line item extracted from invoice sheet.

    Attributes:
        row: 1-based row number from source sheet.
        part_no: Part number (required).
        po_no: Purchase order number (required).
        qty: Quantity (required).
        price: Unit price (required).
        amount: Total amount (required).
        currency: Currency code (required).
        coo: Country of origin (required).
        cod: Country of destination (optional, overrides coo if present).
        brand: Brand name (required).
        brand_type: Brand type classification (required).
        model: Model number (required).
        inv_no: Invoice number (optional, from data row).
        serial: Serial number (optional).
        weight: Allocated net weight (filled by weight allocation).
    """

    row: int
    part_no: str = ""
    po_no: str = ""
    qty: float = 0.0
    price: float = 0.0
    amount: float = 0.0
    currency: str = ""
    coo: str = ""
    cod: str = ""
    brand: str = ""
    brand_type: str = ""
    model: str = ""
    inv_no: str = ""
    serial: str = ""
    weight: float = 0.0


@dataclass
class PackingItem:
    """Single packing line item extracted from packing sheet.

    Attributes:
        row: 1-based row number from source sheet.
        part_no: Part number (required, must match invoice).
        qty: Quantity (required).
        nw: Net weight in KG (required).
        gw: Gross weight in KG (required).
        pack: Number of packages (optional).
    """

    row: int
    part_no: str = ""
    qty: float = 0.0
    nw: float = 0.0
    gw: float = 0.0
    pack: float = 0.0


@dataclass
class PackingTotals:
    """Total values extracted from packing sheet total row.

    Attributes:
        total_row: 1-based row number of the total row.
        total_nw: Total net weight (required for output).
        total_gw: Total gross weight (required for output).
        total_packets: Total packages (optional).
        nw_precision: Detected decimal precision for total_nw.
        gw_precision: Detected decimal precision for total_gw.
    """

    total_row: int = 0
    total_nw: Decimal = field(default_factory=lambda: Decimal("0"))
    total_gw: Decimal = field(default_factory=lambda: Decimal("0"))
    total_packets: int | None = None
    nw_precision: int = 2
    gw_precision: int = 2


@dataclass
class ValidationResult:
    """Result of validation containing errors and warnings.

    Attributes:
        errors: List of error tuples (code, message).
        warnings: List of warning tuples (code, message).
    """

    errors: list[tuple[str, str]] = field(default_factory=list)
    warnings: list[tuple[str, str]] = field(default_factory=list)

    def add_error(self, code: str, message: str, log: bool = True) -> None:
        """Add an error.

        Args:
            code (str): Error code.
            message (str): Error message.
            log (bool): Whether to log this error (default True).
        """
        self.errors.append((code, message))
        if log:
            from autoconvert.logging import log_error_code

            log_error_code(code, message)

    def add_warning(self, code: str, message: str, log: bool = True) -> None:
        """Add a warning.

        Args:
            code (str): Warning code.
            message (str): Warning message.
            log (bool): Whether to log this warning (default True).
        """
        self.warnings.append((code, message))
        if log:
            from autoconvert.logging import log_warning_code

            log_warning_code(code, message)

    def has_errors(self) -> bool:
        """Check if there are any errors.

        Returns:
            bool: True if errors exist.
        """
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """Check if there are any warnings.

        Returns:
            bool: True if warnings exist.
        """
        return len(self.warnings) > 0

    def merge(self, other: "ValidationResult") -> None:
        """Merge another ValidationResult into this one.

        Args:
            other (ValidationResult): Another validation result to merge.
        """
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)


@dataclass
class ProcessingResult:
    """Result of processing a single file.

    Attributes:
        status: Processing status (SUCCESS, ATTENTION, or FAILED).
        errors: List of error tuples (code, message).
        warnings: List of warning tuples (code, message).
        output_path: Path to generated output file, if successful.
        invoice_items: Extracted and transformed invoice items.
        packing_items: Extracted packing items.
        packing_totals: Extracted packing totals.
    """

    status: Literal["SUCCESS", "ATTENTION", "FAILED"] = "SUCCESS"
    errors: list[tuple[str, str]] = field(default_factory=list)
    warnings: list[tuple[str, str]] = field(default_factory=list)
    output_path: Path | None = None
    invoice_items: list[InvoiceItem] = field(default_factory=list)
    packing_items: list[PackingItem] = field(default_factory=list)
    packing_totals: PackingTotals | None = None


@dataclass
class BatchSummary:
    """Summary of batch processing results.

    Attributes:
        total_files: Total number of files processed.
        success_count: Number of files with SUCCESS status.
        attention_count: Number of files with ATTENTION status.
        failed_count: Number of files with FAILED status.
        processing_time: Total processing time in seconds.
        failed_files: Dict mapping filename to list of error messages.
        attention_files: Dict mapping filename to list of warning messages.
    """

    total_files: int = 0
    success_count: int = 0
    attention_count: int = 0
    failed_count: int = 0
    processing_time: float = 0.0
    failed_files: dict[str, list[str]] = field(default_factory=dict)
    attention_files: dict[str, list[str]] = field(default_factory=dict)
