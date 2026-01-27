"""Compiled pattern registry for efficient regex matching."""

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FieldPattern:
    """Pattern configuration for a single field.

    Attributes:
        patterns: List of compiled regex patterns.
        field_type: Data type (string, numeric, date, currency).
        required: Whether this field is required.
    """

    patterns: list[re.Pattern[str]] = field(default_factory=list)
    field_type: str = "string"
    required: bool = False


@dataclass
class PatternRegistry:
    """Registry of compiled patterns for sheet and column matching.

    Attributes:
        invoice_sheet_patterns: Patterns for invoice sheet detection.
        packing_sheet_patterns: Patterns for packing sheet detection.
        invoice_columns: Dict of field name to FieldPattern for invoice.
        packing_columns: Dict of field name to FieldPattern for packing.
        inv_no_patterns: Patterns for embedded invoice number extraction.
        inv_no_label_patterns: Patterns for invoice number label detection.
        inv_no_exclude_patterns: Patterns to exclude invalid invoice numbers.
    """

    invoice_sheet_patterns: list[re.Pattern[str]] = field(default_factory=list)
    packing_sheet_patterns: list[re.Pattern[str]] = field(default_factory=list)
    invoice_columns: dict[str, FieldPattern] = field(default_factory=dict)
    packing_columns: dict[str, FieldPattern] = field(default_factory=dict)
    inv_no_patterns: list[re.Pattern[str]] = field(default_factory=list)
    inv_no_label_patterns: list[re.Pattern[str]] = field(default_factory=list)
    inv_no_exclude_patterns: list[re.Pattern[str]] = field(default_factory=list)

    def get_required_invoice_fields(self) -> list[str]:
        """Get list of required invoice field names.

        Returns:
            list[str]: Required field names.
        """
        return [name for name, fp in self.invoice_columns.items() if fp.required]

    def get_required_packing_fields(self) -> list[str]:
        """Get list of required packing field names.

        Returns:
            list[str]: Required field names.
        """
        return [name for name, fp in self.packing_columns.items() if fp.required]


def build_registry(config: dict[str, Any]) -> PatternRegistry:
    """Build pattern registry from parsed YAML configuration.

    Args:
        config (dict[str, Any]): Parsed field_patterns.yaml content.

    Returns:
        PatternRegistry: Registry with all compiled patterns.
    """
    from autoconvert.setup.loader import compile_patterns

    registry = PatternRegistry()

    # Sheet patterns
    if "invoice_sheet" in config:
        patterns = config["invoice_sheet"].get("patterns", [])
        registry.invoice_sheet_patterns = compile_patterns(patterns, "invoice_sheet")

    if "packing_sheet" in config:
        patterns = config["packing_sheet"].get("patterns", [])
        registry.packing_sheet_patterns = compile_patterns(patterns, "packing_sheet")

    # Invoice column patterns
    if "invoice_columns" in config:
        for field_name, field_config in config["invoice_columns"].items():
            if not isinstance(field_config, dict):
                continue

            patterns = field_config.get("patterns", [])
            fp = FieldPattern(
                patterns=compile_patterns(patterns, f"invoice_columns.{field_name}"),
                field_type=field_config.get("type", "string"),
                required=field_config.get("required", False),
            )
            registry.invoice_columns[field_name] = fp

    # Packing column patterns
    if "packing_columns" in config:
        for field_name, field_config in config["packing_columns"].items():
            if not isinstance(field_config, dict):
                continue

            patterns = field_config.get("patterns", [])
            fp = FieldPattern(
                patterns=compile_patterns(patterns, f"packing_columns.{field_name}"),
                field_type=field_config.get("type", "string"),
                required=field_config.get("required", False),
            )
            registry.packing_columns[field_name] = fp

    # Invoice number header extraction patterns
    if "inv_no_cell" in config:
        inv_no_config = config["inv_no_cell"]

        if "patterns" in inv_no_config:
            registry.inv_no_patterns = compile_patterns(
                inv_no_config["patterns"], "inv_no_cell.patterns"
            )

        if "label_patterns" in inv_no_config:
            registry.inv_no_label_patterns = compile_patterns(
                inv_no_config["label_patterns"], "inv_no_cell.label_patterns"
            )

        if "exclude_patterns" in inv_no_config:
            registry.inv_no_exclude_patterns = compile_patterns(
                inv_no_config["exclude_patterns"], "inv_no_cell.exclude_patterns"
            )

    return registry
