"""Configuration validation utilities."""

# Note: Main validation logic is in loader.py (validate_yaml_structure, compile_patterns)
# This module is kept for potential future validation extensions.

from typing import Any


def validate_column_config(config: dict[str, Any], column_type: str) -> list[str]:
    """Validate column configuration structure.

    Args:
        config (dict[str, Any]): Column configuration dict.
        column_type (str): "invoice" or "packing".

    Returns:
        list[str]: List of validation errors (empty if valid).
    """
    errors = []

    for field_name, field_config in config.items():
        if not isinstance(field_config, dict):
            errors.append(
                f"{column_type}_columns.{field_name}: expected dict, got {type(field_config).__name__}"
            )
            continue

        if "patterns" not in field_config:
            errors.append(f"{column_type}_columns.{field_name}: missing 'patterns' key")
        elif not isinstance(field_config["patterns"], list):
            errors.append(
                f"{column_type}_columns.{field_name}.patterns: expected list, got "
                f"{type(field_config['patterns']).__name__}"
            )

        if "type" in field_config:
            valid_types = {"string", "numeric", "date", "currency"}
            if field_config["type"] not in valid_types:
                errors.append(
                    f"{column_type}_columns.{field_name}.type: invalid value "
                    f"'{field_config['type']}', expected one of {valid_types}"
                )

    return errors
