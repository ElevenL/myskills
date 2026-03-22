#!/usr/bin/env python3
"""
WASDE (World Agricultural Supply and Demand Estimates) Report Generator.

Generates formatted supply and demand reports for agricultural commodities.
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

# Commodity codes
COMMODITY_CODES = {
    "soybean": "2222000",
    "corn": "0410000",
    "wheat": "0411000",
    "cotton": "0231000"
}

# Base URL
BASE_URL = "https://api.fas.usda.gov/api"


def get_api_key():
    """Get API key from environment."""
    key = os.environ.get("USDA_FAS_API_KEY")
    if not key:
        print("Error: USDA_FAS_API_KEY not set", file=sys.stderr)
        print("Get your API key from https://api.data.gov", file=sys.stderr)
        sys.exit(1)
    return key


def make_request(endpoint):
    """Make API request."""
    headers = {
        "Accept": "application/json",
        "X-Api-Key": get_api_key()
    }
    url = f"{BASE_URL}{endpoint}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_attributes_map():
    """Get attribute ID to name mapping."""
    data = make_request("/psd/commodityAttributes")
    return {str(item["attributeId"]): item["attributeName"] for item in data}


def get_world_data(commodity_code, market_year):
    """Get world-level data."""
    return make_request(f"/psd/commodity/{commodity_code}/world/year/{market_year}")


def get_country_data(commodity_code, market_year):
    """Get all countries data."""
    return make_request(f"/psd/commodity/{commodity_code}/country/all/year/{market_year}")


def parse_supply_demand(data: List[Dict], country: str, attrs_map: Dict) -> Dict:
    """Parse raw PSD data into supply/demand report."""
    result = {
        "Country": country.upper(),
        "MarketYear": None,
        "CalendarYear": None,
        "Month": None,
        "yearMonth": None,
        "Area_Harvested": None,
        "Area_Planted": None,
        "Yield": None,
        "Beginning_Stocks": None,
        "Production": None,
        "Imports": None,
        "Total_Supply": None,
        "Crush": None,
        "Total_Domestic": None,
        "Exports": None,
        "Ending_Stocks": None,
        "pddt": None,  # Production + Imports / Total Demand
        "esdt": None,  # Ending Stocks / Total Demand
    }

    for item in data:
        attr_name = attrs_map.get(str(item.get("attributeId", "")), "")

        if attr_name == "Area Harvested":
            result["MarketYear"] = item.get("marketYear")
            result["CalendarYear"] = item.get("calendarYear")
            result["Month"] = item.get("month")
            # Convert hectares to million hectares
            result["Area_Harvested"] = round(item.get("value", 0) * 0.0024711, 1)
            result["Area_Planted"] = result["Area_Harvested"]

            month = item.get("month", "")
            if month in ["05", "06", "07", "08", "09", "10", "11", "12"]:
                result["yearMonth"] = item.get("marketYear", "") + month
            else:
                my = item.get("marketYear", "")
                result["yearMonth"] = str(int(my) + 1) + month if my else None

        elif attr_name == "Area Planted":
            result["Area_Planted"] = round(item.get("value", 0) * 0.0024711, 1)

        elif attr_name == "Yield":
            # Convert to tonnes/hectare
            result["Yield"] = round(item.get("value", 0) / 0.0672, 2)

        elif attr_name == "Beginning Stocks":
            result["Beginning_Stocks"] = round(item.get("value", 0) / 1000, 2)

        elif attr_name == "Production":
            result["Production"] = round(item.get("value", 0) / 1000, 2)

        elif attr_name == "Imports":
            result["Imports"] = round(item.get("value", 0) / 1000, 2)

        elif attr_name == "Total Supply":
            result["Total_Supply"] = round(item.get("value", 0) / 1000, 2)

        elif attr_name in ["Crush", "Crush (MT)"]:
            result["Crush"] = round(item.get("value", 0) / 1000, 2)

        elif attr_name == "Total Distribution":
            result["Total_Domestic"] = round(item.get("value", 0) / 1000, 2)

        elif attr_name in ["Exports", "MY Exports"]:
            result["Exports"] = round(item.get("value", 0) / 1000, 2)

        elif attr_name in ["Ending Stocks", "Ending Stocks (MT)"]:
            result["Ending_Stocks"] = round(item.get("value", 0) / 1000, 2)

    # Calculate ratios
    total_supply = (result["Production"] or 0) + (result["Imports"] or 0)
    total_demand = (result["Exports"] or 0) + (result["Total_Domestic"] or 0)

    if total_demand > 0:
        result["pddt"] = round(total_supply / total_demand, 4)
        result["esdt"] = round((result["Ending_Stocks"] or 0) / total_demand, 4)

    return result


def generate_report(commodity: str, country: str, market_year: str, output_format: str = "table") -> None:
    """Generate WASDE report for a commodity and country."""

    commodity_code = COMMODITY_CODES.get(commodity.lower())
    if not commodity_code:
        print(f"Error: Unknown commodity '{commodity}'", file=sys.stderr)
        print(f"Available commodities: {', '.join(COMMODITY_CODES.keys())}", file=sys.stderr)
        sys.exit(1)

    attrs_map = get_attributes_map()

    # Fetch data
    if country.upper() == "WORLD":
        raw_data = get_world_data(commodity_code, market_year)
        country_data = raw_data
    else:
        raw_data = get_country_data(commodity_code, market_year)
        country_data = [d for d in raw_data if d.get("countryCode") == country.upper()]

    if not country_data:
        print(f"No data found for {country} in {market_year}", file=sys.stderr)
        sys.exit(1)

    # Parse report
    report = parse_supply_demand(country_data, country, attrs_map)

    # Output
    if output_format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_wadse_table(report, commodity)


def print_wadse_table(report: Dict, commodity: str) -> None:
    """Print WASDE report as formatted table."""
    print(f"\n{'='*60}")
    print(f"WASDE Report: {commodity.upper()} - {report['Country']}")
    print(f"Market Year: {report['MarketYear']} | Month: {report['Month']}")
    print(f"{'='*60}")

    print(f"\n{'SUPPLY':^30}")
    print(f"{'-'*30}")
    print(f"  Area Harvested (Mha):  {report['Area_Harvested'] or 'N/A':>10}")
    print(f"  Area Planted (Mha):    {report['Area_Planted'] or 'N/A':>10}")
    print(f"  Yield (t/ha):          {report['Yield'] or 'N/A':>10}")
    print(f"  Beginning Stocks (Mt): {report['Beginning_Stocks'] or 'N/A':>10}")
    print(f"  Production (Mt):       {report['Production'] or 'N/A':>10}")
    print(f"  Imports (Mt):          {report['Imports'] or 'N/A':>10}")

    print(f"\n{'DEMAND':^30}")
    print(f"{'-'*30}")
    print(f"  Crush (Mt):            {report['Crush'] or 'N/A':>10}")
    print(f"  Total Domestic (Mt):   {report['Total_Domestic'] or 'N/A':>10}")
    print(f"  Exports (Mt):          {report['Exports'] or 'N/A':>10}")
    print(f"  Ending Stocks (Mt):    {report['Ending_Stocks'] or 'N/A':>10}")

    print(f"\n{'RATIOS':^30}")
    print(f"{'-'*30}")
    print(f"  PDDT: {report['pddt'] or 'N/A':>10}")
    print(f"  ESDT: {report['esdt'] or 'N/A':>10}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Generate WASDE supply/demand reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # US soybean report for 2024/25 market year
  python wasde_report.py soybean --country US --year 2024

  # Brazil soybean report
  python wasde_report.py soybean --country BR --year 2024

  # World soybean report
  python wasde_report.py soybean --country WORLD --year 2024

  # Output as JSON
  python wasde_report.py soybean --country US --year 2024 --format json
        """
    )
    parser.add_argument(
        "commodity",
        choices=list(COMMODITY_CODES.keys()),
        help="Commodity name"
    )
    parser.add_argument(
        "--country", "-c",
        required=True,
        help="Country code (US, BR, AR, WORLD, etc.)"
    )
    parser.add_argument(
        "--year", "-y",
        required=True,
        help="Market year (e.g., 2024 for 2024/25)"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["table", "json"],
        default="table",
        help="Output format"
    )

    args = parser.parse_args()
    generate_report(args.commodity, args.country, args.year, args.format)


if __name__ == "__main__":
    main()