"""Setup module - configuration loading and validation."""

from autoconvert.setup.config import Config, load_all_config
from autoconvert.setup.registry import PatternRegistry

__all__ = [
    "Config",
    "load_all_config",
    "PatternRegistry",
]
