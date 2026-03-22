---
name: USDA Reports
description: Tools for fetching USDA agricultural reports including WASDE supply/demand data, crop progress, and condition reports. Use when user asks for: (1) WASDE soybean/corn supply and demand data, (2) US crop progress reports, (3) Crop condition ratings, (4) USDA PSD data, (5) NASS QuickStats data.
---

# USDA Reports Skill

This skill provides tools to fetch USDA agricultural reports including Production, Supply, and Distribution (PSD) data and NASS QuickStats crop progress data.

## Quick Start

### WASDE Supply/Demand Reports

Get soybean supply and demand data:

```bash
python scripts/wasde_report.py soybean --country US --year 2024
python scripts/wasde_report.py soybean --country BR --year 2024
python scripts/wasde_report.py soybean --country WORLD --year 2024
```

Get corn supply and demand data:

```bash
python scripts/wasde_report.py corn --country US --year 2024
```

### Crop Progress Reports

Get US crop condition ratings:

```bash
python scripts/crop_progress.py condition --commodity SOYBEANS --year 2024
```

Get planting/harvesting progress:

```bash
python scripts/crop_progress.py progress --commodity SOYBEANS --unit PLANTED --year 2024
python scripts/crop_progress.py progress --commodity SOYBEANS --unit HARVESTED --year 2024
python scripts/crop_progress.py progress --commodity SOYBEANS --unit BLOOMING --year 2024
```

### Raw API Access

Fetch raw PSD data:

```bash
python scripts/usda_api.py psd-world <commodity_code> <market_year>
python scripts/usda_api.py psd-country <commodity_code> <country_code> <market_year>
```

Fetch QuickStats data:

```bash
python scripts/usda_api.py quickstats --commodity SOYBEANS --category CONDITION --year 2024
```

## Commodity Codes

Common commodity codes for PSD API:

| Commodity | Code |
|-----------|------|
| Soybean | 2222000 |
| Corn | 0410000 |
| Wheat | 0411000 |
| Cotton | 0231000 |

Common country codes: `US` (United States), `BR` (Brazil), `AR` (Argentina)

## Market Year

For soybeans, market year runs from May to April. Use the starting year (e.g., 2024 for 2024/25 market year).

## API Keys

Scripts automatically load environment variables from `~/.env` file. Or set them manually:

```bash
export USDA_FAS_API_KEY="your_fas_api_key"
export USDA_NASS_API_KEY="your_nass_api_key"
```

Get API keys from:
- FAS API: https://api.data.gov
- NASS QuickStats: https://quickstats.nass.usda.gov/api