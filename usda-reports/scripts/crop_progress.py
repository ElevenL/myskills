#!/usr/bin/env python3
"""
US Crop Progress and Condition Report Tool.

Fetches crop progress and condition data from USDA NASS QuickStats API.
"""
import os
import sys
import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests


def load_env_from_home():
    """Load environment variables from ~/.env file."""
    env_file = Path.home() / ".env"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip()
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    if key and key not in os.environ:
                        os.environ[key] = value


load_env_from_home()

BASE_URL = "https://quickstats.nass.usda.gov/api"


def get_api_key():
    """Get API key from environment."""
    key = os.environ.get("USDA_NASS_API_KEY")
    if not key:
        print("Error: USDA_NASS_API_KEY not set", file=sys.stderr)
        print("Get your API key from https://quickstats.nass.usda.gov/api", file=sys.stderr)
        sys.exit(1)
    return key


def query_quickstats(params: Dict) -> List[Dict]:
    """Query NASS QuickStats API."""
    params = dict(params)
    params["key"] = get_api_key()
    params["format"] = "json"

    url = f"{BASE_URL}/api_GET/"
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json().get("data", [])


def get_condition_report(commodity: str, year: str) -> List[Dict]:
    """
    Get crop condition report.

    Returns weekly condition ratings (Excellent, Good, Fair, Poor, Very Poor).
    """
    params = {
        "source_desc": "SURVEY",
        "sector_desc": "CROPS",
        "group_desc": "FIELD CROPS",
        "commodity_desc": commodity.upper(),
        "statisticcat_desc": "CONDITION",
        "agg_level_desc": "NATIONAL",
        "state_name": "US TOTAL",
        "year": str(year)
    }

    data = query_quickstats(params)

    # Pivot data by week
    weekly_data = {}
    for item in data:
        end_code = item.get("end_code")
        week_ending = item.get("week_ending")
        unit = item.get("unit_desc", "")
        value = item.get("Value")

        if end_code not in weekly_data:
            weekly_data[end_code] = {
                "end_code": end_code,
                "week_ending": week_ending,
                "year": item.get("year"),
                "commodity": item.get("commodity_desc"),
                "state": item.get("state_name")
            }

        # Map unit to condition
        unit_map = {
            "PCT EXCELLENT": "EXCELLENT",
            "PCT GOOD": "GOOD",
            "PCT FAIR": "FAIR",
            "PCT POOR": "POOR",
            "PCT VERY POOR": "VERY_POOR"
        }

        if unit in unit_map:
            weekly_data[end_code][unit_map[unit]] = float(value) if value else None

    return list(weekly_data.values())


def get_progress_report(commodity: str, year: str, unit: str) -> List[Dict]:
    """
    Get crop progress report.

    unit options: PLANTED, HARVESTED, EMERGED, BLOOMING, DROPPING LEAVES, SETTING PODS
    """
    params = {
        "source_desc": "SURVEY",
        "sector_desc": "CROPS",
        "group_desc": "FIELD CROPS",
        "commodity_desc": commodity.upper(),
        "statisticcat_desc": "PROGRESS",
        "agg_level_desc": "NATIONAL",
        "state_name": "US TOTAL",
        "year": str(year)
    }

    data = query_quickstats(params)

    # Filter by unit
    unit_desc = f"PCT {unit}"
    filtered = [d for d in data if d.get("unit_desc") == unit_desc]

    result = []
    for item in filtered:
        result.append({
            "Country": item.get("state_alpha"),
            "year": item.get("year"),
            "commodity": item.get("commodity_desc"),
            "state": item.get("state_name"),
            "end_code": item.get("end_code"),
            "week_ending": item.get("week_ending"),
            "unit": unit.lower().replace(" ", "_"),
            "value": float(item.get("Value")) if item.get("Value") else None
        })

    return result


def print_condition_table(data: List[Dict]) -> None:
    """Print condition report as table."""
    if not data:
        print("No data found")
        return

    print(f"\n{'='*80}")
    print(f"US Crop Condition Report: {data[0].get('commodity', 'N/A')} - {data[0].get('year', 'N/A')}")
    print(f"{'='*80}")

    header = f"{'Week Ending':<15} {'Excellent':>10} {'Good':>10} {'Fair':>10} {'Poor':>10} {'Very Poor':>10}"
    print(header)
    print("-" * 80)

    # Sort by week ending
    sorted_data = sorted(data, key=lambda x: x.get("week_ending", ""))

    for row in sorted_data:
        excellent = row.get("EXCELLENT", "N/A")
        good = row.get("GOOD", "N/A")
        fair = row.get("FAIR", "N/A")
        poor = row.get("POOR", "N/A")
        very_poor = row.get("VERY_POOR", "N/A")

        def fmt(v):
            return f"{v:.1f}" if isinstance(v, (int, float)) else str(v)

        print(f"{row.get('week_ending', 'N/A'):<15} {fmt(excellent):>10} {fmt(good):>10} {fmt(fair):>10} {fmt(poor):>10} {fmt(very_poor):>10}")

    print(f"{'='*80}\n")


def print_progress_table(data: List[Dict]) -> None:
    """Print progress report as table."""
    if not data:
        print("No data found")
        return

    print(f"\n{'='*60}")
    unit = data[0].get("unit", "progress")
    print(f"US Crop Progress: {data[0].get('commodity', 'N/A')} - {unit.upper()}")
    print(f"Year: {data[0].get('year', 'N/A')}")
    print(f"{'='*60}")

    header = f"{'Week Ending':<15} {'Progress (%)':>15}"
    print(header)
    print("-" * 40)

    sorted_data = sorted(data, key=lambda x: x.get("week_ending", ""))

    for row in sorted_data:
        value = row.get("value")
        value_str = f"{value:.1f}" if isinstance(value, (int, float)) else "N/A"
        print(f"{row.get('week_ending', 'N/A'):<15} {value_str:>15}")

    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="US Crop Progress and Condition Reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get soybean condition ratings for 2024
  python crop_progress.py condition --commodity SOYBEANS --year 2024

  # Get corn planting progress
  python crop_progress.py progress --commodity CORN --unit PLANTED --year 2024

  # Get soybean harvest progress
  python crop_progress.py progress --commodity SOYBEANS --unit HARVESTED --year 2024

  # Get soybean blooming progress
  python crop_progress.py progress --commodity SOYBEANS --unit BLOOMING --year 2024

Progress unit options:
  PLANTED         - Planting progress
  HARVESTED       - Harvest progress
  EMERGED         - Emergence progress
  BLOOMING        - Blooming progress
  DROPPING LEAVES - Leaf dropping progress
  SETTING PODS    - Pod setting progress
        """
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Condition subcommand
    cond_parser = subparsers.add_parser("condition", help="Get crop condition ratings")
    cond_parser.add_argument("--commodity", "-c", default="SOYBEANS", help="Commodity name")
    cond_parser.add_argument("--year", "-y", required=True, help="Year")
    cond_parser.add_argument("--format", "-f", choices=["table", "json"], default="table")

    # Progress subcommand
    prog_parser = subparsers.add_parser("progress", help="Get crop progress")
    prog_parser.add_argument("--commodity", "-c", default="SOYBEANS", help="Commodity name")
    prog_parser.add_argument("--unit", "-u", required=True,
                            help="Progress unit (PLANTED, HARVESTED, EMERGED, BLOOMING, DROPPING LEAVES, SETTING PODS)")
    prog_parser.add_argument("--year", "-y", required=True, help="Year")
    prog_parser.add_argument("--format", "-f", choices=["table", "json"], default="table")

    args = parser.parse_args()

    if args.command == "condition":
        data = get_condition_report(args.commodity, args.year)
        if args.format == "json":
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print_condition_table(data)

    elif args.command == "progress":
        data = get_progress_report(args.commodity, args.year, args.unit)
        if args.format == "json":
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print_progress_table(data)


if __name__ == "__main__":
    main()