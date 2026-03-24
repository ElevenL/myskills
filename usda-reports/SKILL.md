---
name: USDA Reports
description: Tools for fetching USDA agricultural reports including WASDE supply/demand data, crop progress, and condition reports. Use when user asks for: (1) WASDE soybean/corn supply and demand data, (2) US crop progress reports, (3) Crop condition ratings, (4) USDA PSD data, (5) NASS QuickStats data, (6) USDA report schedules/calendar.
---

# USDA Reports Skill

This skill provides tools to fetch USDA agricultural reports including Production, Supply, and Distribution (PSD) data, NASS QuickStats crop progress data, and report schedules.

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

### Report Schedule (Calendar)

Query USDA NASS report release schedules:

```bash
# Show all scheduled reports
python scripts/report_schedule.py list

# Show upcoming reports (next 30 days)
python scripts/report_schedule.py upcoming

# Show upcoming reports in next 7 days
python scripts/report_schedule.py upcoming --days 7

# Filter by report type
python scripts/report_schedule.py list --type "Crop Production"
python scripts/report_schedule.py list --type "Grain Stocks"
python scripts/report_schedule.py list --type "Crop Progress"

# Filter by date range
python scripts/report_schedule.py list --start 2026-04-01 --end 2026-06-30

# Show available report types
python scripts/report_schedule.py types
```

Available report types:
- **Prospective Plantings** (种植意向报告) - Released in March/April
- **Acreage** (种植面积确认报告) - Released in June/July
- **Grain Stocks** (季度库存报告) - Quarterly (Jan, Apr, Jul, Oct)
- **Crop Production** (月度作物产量报告/月度供需报告) - Monthly
- **Crop Progress** (作物进展报告/作物优良率报告) - Weekly during growing season

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