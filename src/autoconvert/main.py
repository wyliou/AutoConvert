"""Main entry point for AutoConvert CLI."""

import argparse
import sys
from pathlib import Path

from autoconvert import __version__
from autoconvert.core.errors import ConfigError
from autoconvert.diagnostic.runner import run_diagnostic
from autoconvert.logging.logger import setup_logging
from autoconvert.output.batch import process_batch
from autoconvert.setup.config import load_all_config


def main() -> int:
    """Main entry point for AutoConvert.

    Returns:
        int: Exit code (0=success, 1=some failures, 2=config error).
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="AutoConvert - Vendor Excel to Customs Template Converter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"AutoConvert v{__version__}",
    )

    parser.add_argument(
        "--diagnose",
        type=str,
        metavar="FILENAME",
        help="Run diagnostic mode on a single file",
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config",
        help="Path to config folder (default: config)",
    )

    args = parser.parse_args()

    # Set up logging
    setup_logging()

    # Load configuration
    try:
        config = load_all_config(Path(args.config))
    except ConfigError as e:
        print(f"[ERROR] {e}")
        _pause_if_interactive()
        return 2

    # Run diagnostic mode if requested
    if args.diagnose:
        file_path = Path(args.diagnose)
        if not file_path.exists():
            # Try in data folder
            file_path = config.data_folder / args.diagnose

        if not file_path.exists():
            print(f"[ERROR] File not found: {args.diagnose}")
            _pause_if_interactive()
            return 2

        exit_code = run_diagnostic(file_path, config)
        _pause_if_interactive()
        return exit_code

    # Run batch processing
    summary = process_batch(config)

    _pause_if_interactive()
    return 1 if summary.failed_count > 0 else 0


def _pause_if_interactive() -> None:
    """Pause for user review if running interactively (double-clicked .exe).

    Checks if running without arguments (typical double-click behavior).
    """
    if hasattr(sys, "frozen"):
        # Running as PyInstaller executable
        input("\nPress Enter to exit...")
    # In normal terminal usage, don't pause


if __name__ == "__main__":
    sys.exit(main())
