# AutoConvert

CLI tool for converting vendor Excel files to standardized customs templates.

## Installation

```bash
uv sync
```

## Usage

### Batch Processing

```bash
uv run autoconvert
```

### Diagnostic Mode

```bash
uv run autoconvert --diagnose filename.xlsx
```

## Configuration

Configuration files are located in the `config/` folder:

- `field_patterns.yaml` - Column mapping patterns (regex-based)
- `currency_rules.xlsx` - Currency name to code mappings
- `country_rules.xlsx` - Country name to code mappings
- `output_template.xlsx` - 40-column template file

## Folder Structure

```
data/           - Input files (vendor Excel files)
data/finished/  - Output files (generated templates)
config/         - Configuration files
```
