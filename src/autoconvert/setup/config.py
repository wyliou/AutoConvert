"""Main configuration loading and Config dataclass."""

from dataclasses import dataclass, field
from pathlib import Path

from autoconvert.setup.loader import (
    load_lookup_table,
    load_yaml_config,
    validate_template,
    validate_yaml_structure,
)
from autoconvert.setup.registry import PatternRegistry, build_registry


@dataclass
class Config:
    """Application configuration loaded from config folder.

    Attributes:
        registry: Compiled pattern registry for matching.
        currency_rules: Currency name to code mapping.
        country_rules: Country name to code mapping.
        template_path: Path to output template file.
        data_folder: Path to input data folder.
        output_folder: Path to output folder.
    """

    registry: PatternRegistry = field(default_factory=PatternRegistry)
    currency_rules: dict[str, str] = field(default_factory=dict)
    country_rules: dict[str, str] = field(default_factory=dict)
    template_path: Path = field(default_factory=lambda: Path("config/output_template.xlsx"))
    data_folder: Path = field(default_factory=lambda: Path("data"))
    output_folder: Path = field(default_factory=lambda: Path("data/finished"))


def load_all_config(config_folder: Path | None = None) -> Config:
    """Load all configuration files and return Config object.

    Args:
        config_folder (Path | None): Path to config folder. Defaults to ./config.

    Returns:
        Config: Fully loaded configuration.

    Raises:
        ConfigError: If any configuration file is invalid.
    """
    if config_folder is None:
        config_folder = Path("config")

    # Load and validate YAML patterns
    yaml_path = config_folder / "field_patterns.yaml"
    yaml_config = load_yaml_config(yaml_path)
    validate_yaml_structure(yaml_config)
    registry = build_registry(yaml_config)

    # Load lookup tables
    currency_path = config_folder / "currency_rules.xlsx"
    currency_rules = load_lookup_table(currency_path)

    country_path = config_folder / "country_rules.xlsx"
    country_rules = load_lookup_table(country_path)

    # Validate template
    template_path = config_folder / "output_template.xlsx"
    validate_template(template_path)

    # Create output folder if it doesn't exist
    data_folder = Path("data")
    output_folder = data_folder / "finished"
    output_folder.mkdir(parents=True, exist_ok=True)

    return Config(
        registry=registry,
        currency_rules=currency_rules,
        country_rules=country_rules,
        template_path=template_path,
        data_folder=data_folder,
        output_folder=output_folder,
    )
