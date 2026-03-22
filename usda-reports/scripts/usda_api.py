#!/usr/bin/env python3
"""
USDA API wrapper for PSD and QuickStats APIs.
"""
import os
import sys
import argparse
import json
import requests
from pathlib import Path


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
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    # Only set if not already in environment
                    if key and key not in os.environ:
                        os.environ[key] = value


# Load env on module import
load_env_from_home()

# API Base URLs
FAS_BASE_URL = "https://api.fas.usda.gov/api"
NASS_BASE_URL = "https://quickstats.nass.usda.gov/api"


def get_fas_api_key():
    """Get FAS API key from environment."""
    key = os.environ.get("USDA_FAS_API_KEY")
    if not key:
        print("Error: USDA_FAS_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    return key


def get_nass_api_key():
    """Get NASS API key from environment."""
    key = os.environ.get("USDA_NASS_API_KEY")
    if not key:
        print("Error: USDA_NASS_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    return key


def fas_request(endpoint):
    """Make request to FAS API."""
    headers = {
        "Accept": "application/json",
        "X-Api-Key": get_fas_api_key()
    }
    url = f"{FAS_BASE_URL}{endpoint}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def nass_request(params):
    """Make request to NASS QuickStats API."""
    params = dict(params)
    params["key"] = get_nass_api_key()
    params["format"] = "json"
    url = f"{NASS_BASE_URL}/api_GET/"
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json().get("data", [])


# PSD API Functions
def get_psd_attributes():
    """Get commodity attributes mapping."""
    data = fas_request("/psd/commodityAttributes")
    return {str(item["attributeId"]): item["attributeName"] for item in data}


def get_psd_commodities():
    """Get list of commodities."""
    return fas_request("/psd/commodities")


def get_psd_countries():
    """Get list of countries."""
    return fas_request("/psd/countries")


def get_psd_world_data(commodity_code, market_year):
    """Get world PSD data for a commodity."""
    return fas_request(f"/psd/commodity/{commodity_code}/world/year/{market_year}")


def get_psd_country_data(commodity_code, country_code, market_year):
    """Get country PSD data for a commodity."""
    return fas_request(f"/psd/commodity/{commodity_code}/country/{country_code}/year/{market_year}")


def get_psd_all_countries_data(commodity_code, market_year):
    """Get all countries PSD data for a commodity."""
    return fas_request(f"/psd/commodity/{commodity_code}/country/all/year/{market_year}")


# QuickStats API Functions
def get_quickstats_data(params):
    """Get data from NASS QuickStats API."""
    return nass_request(params)


def main():
    parser = argparse.ArgumentParser(description="USDA API Client")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # PSD commands
    subparsers.add_parser("psd-attributes", help="Get PSD attributes")
    subparsers.add_parser("psd-commodities", help="Get PSD commodities")
    subparsers.add_parser("psd-countries", help="Get PSD countries")

    psd_world = subparsers.add_parser("psd-world", help="Get world PSD data")
    psd_world.add_argument("commodity_code", help="Commodity code")
    psd_world.add_argument("market_year", help="Market year")

    psd_country = subparsers.add_parser("psd-country", help="Get country PSD data")
    psd_country.add_argument("commodity_code", help="Commodity code")
    psd_country.add_argument("country_code", help="Country code")
    psd_country.add_argument("market_year", help="Market year")

    psd_all = subparsers.add_parser("psd-all", help="Get all countries PSD data")
    psd_all.add_argument("commodity_code", help="Commodity code")
    psd_all.add_argument("market_year", help="Market year")

    # QuickStats commands
    qs = subparsers.add_parser("quickstats", help="Query QuickStats API")
    qs.add_argument("--source", default="SURVEY", help="Source description")
    qs.add_argument("--sector", default="CROPS", help="Sector description")
    qs.add_argument("--group", default="FIELD CROPS", help="Group description")
    qs.add_argument("--commodity", required=True, help="Commodity description")
    qs.add_argument("--category", required=True, help="Statistic category")
    qs.add_argument("--year", required=True, help="Year")
    qs.add_argument("--level", default="NATIONAL", help="Aggregation level")
    qs.add_argument("--state", default="US TOTAL", help="State name")

    args = parser.parse_args()

    if args.command == "psd-attributes":
        result = get_psd_attributes()
    elif args.command == "psd-commodities":
        result = get_psd_commodities()
    elif args.command == "psd-countries":
        result = get_psd_countries()
    elif args.command == "psd-world":
        result = get_psd_world_data(args.commodity_code, args.market_year)
    elif args.command == "psd-country":
        result = get_psd_country_data(args.commodity_code, args.country_code, args.market_year)
    elif args.command == "psd-all":
        result = get_psd_all_countries_data(args.commodity_code, args.market_year)
    elif args.command == "quickstats":
        params = {
            "source_desc": args.source,
            "sector_desc": args.sector,
            "group_desc": args.group,
            "commodity_desc": args.commodity,
            "statisticcat_desc": args.category,
            "agg_level_desc": args.level,
            "state_name": args.state,
            "year": args.year
        }
        result = get_quickstats_data(params)

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()