---
name: USDA FAS PSD & ESR Data API
description: Tools for interacting with the Production, Supply and Distribution (PSD) Forecast Data API and Export Sales Reporting (ESR) Data API of World Agricultural Commodities from USDA FAS.
---

# USDA FAS PSD & ESR Data API Skill

This skill provides a Python interface to query the USDA FAS Open Data API for Production, Supply, and Distribution (PSD) data, as well as Export Sales Reporting (ESR) data.

## Configuration

To use the scripts in this skill, you must set your API Key. You can obtain an API key by signing up at [API.Data.Gov](https://api.data.gov).

Set the environment variable:
```bash
export USDA_API_KEY="your_actual_api_key_here"
```

## Available Scripts

### `usda_psd_api.py`

This script provides a command-line interface to fetch various data endpoints. When using this script, ensure you are in the directory containing the script or provide its full path.

**To get help and view available commands:**
```bash
python .agent/skills/usda-fas-psd-api/usda_psd_api.py --help
```

**Common Commands:**
1.  **Get Commodity Attributes:**
    Fetch attribute names and their corresponding IDs.
    ```bash
    python .agent/skills/usda-fas-psd-api/usda_psd_api.py attributes
    ```

2.  **Get Commodities:**
    Fetch the list of registered commodities.
    ```bash
    python .agent/skills/usda-fas-psd-api/usda_psd_api.py commodities
    ```

3.  **Get Countries:**
    Fetch the list of supported countries and their codes.
    ```bash
    python .agent/skills/usda-fas-psd-api/usda_psd_api.py countries
    ```

5.  **Get ESR Global Exports Data:**
    Fetch ESR exports data for a specific commodity globally. (e.g., commodity code 101 for wheat, market year 2023)
    ```bash
    python .agent/skills/usda-fas-psd-api/usda_psd_api.py esr-exports-all <commodity_code> <market_year>
    ```

## Python Integration
If you are writing other python scripts and need to fetch this data, you can import functions from `usda_psd_api.py`:

```python
import sys
# Ensure the skill path is in your python path if not running from the skill directory
sys.path.append(".agent/skills/usda-fas-psd-api/")

from usda_psd_api import get_commodity_attributes

# Note: requires USDA_API_KEY env variable set
attributes = get_commodity_attributes()
print(attributes)
```

## Endpoints Implemented

**PSD Endpoints:**
- `GET /api/psd/commodityAttributes`
- `GET /api/psd/commodities`
- `GET /api/psd/countries`
- `GET /api/psd/regions`
- `GET /api/psd/unitsOfMeasure`
- `GET /api/psd/commodity/{commodityCode}/world/year/{marketYear}`
- `GET /api/psd/commodity/{commodityCode}/country/{countryCode}/year/{marketYear}`

**ESR Endpoints:**
- `GET /api/esr/commodities`
- `GET /api/esr/countries`
- `GET /api/esr/datareleasedates`
- `GET /api/esr/regions`
- `GET /api/esr/unitsOfMeasure`
- `GET /api/esr/exports/commodityCode/{commodityCode}/allCountries/marketYear/{marketYear}`
- `GET /api/esr/exports/commodityCode/{commodityCode}/countryCode/{countryCode}/marketYear/{marketYear}`
