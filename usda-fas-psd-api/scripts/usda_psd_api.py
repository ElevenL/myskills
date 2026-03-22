import os
import requests
import json
import argparse
import sys

# Base URL for the USDA Open Data API
BASE_URL = "https://api.fas.usda.gov/api"


def get_api_key():
    """Retrieve the USDA API key from the environment."""
    api_key = os.environ.get("USDA_API_KEY")
    if not api_key:
        print("Error: USDA_API_KEY environment variable not set.", file=sys.stderr)
        print("Please set it using: export USDA_API_KEY='your_api_key'", file=sys.stderr)
        sys.exit(1)
    return api_key


def make_request(endpoint, params=None):
    """Make a GET request to the USDA API."""
    api_key = get_api_key()
    headers = {
        "X-Api-Key": api_key,
        "Accept": "application/json"
    }
    url = f"{BASE_URL}{endpoint}"

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making request to {url}: {e}", file=sys.stderr)
        if response is not None and response.text:
            print(f"Response: {response.text}", file=sys.stderr)
        sys.exit(1)


def get_commodity_attributes():
    """Returns a set of records with data for Commodity Attribute Names and their corresponding Attribute IDs."""
    return make_request("/psd/commodityAttributes")


def get_commodities():
    """Returns a list of commodities."""
    return make_request("/psd/commodities")


def get_countries():
    """Returns a list of countries."""
    return make_request("/psd/countries")


def get_regions():
    """Returns a list of regions."""
    return make_request("/psd/regions")


def get_units_of_measure():
    """Returns a list of units of measure."""
    return make_request("/psd/unitsOfMeasure")


def get_commodity_world_data(commodity_code, market_year):
    """Returns world PSD data for a specific commodity and market year."""
    return make_request(f"/psd/commodity/{commodity_code}/world/year/{market_year}")


def get_commodity_country_data(commodity_code, country_code, market_year):
    """Returns PSD data for a specific commodity, country and market year."""
    return make_request(f"/psd/commodity/{commodity_code}/country/{country_code}/year/{market_year}")


# ESR endpoints
def get_esr_commodities():
    """Returns a list of commodities for ESR."""
    return make_request("/esr/commodities")


def get_esr_countries():
    """Returns a list of countries for ESR."""
    return make_request("/esr/countries")


def get_esr_datareleasedates():
    """Returns a list of data release dates for ESR."""
    return make_request("/esr/datareleasedates")


def get_esr_regions():
    """Returns a list of regions for ESR."""
    return make_request("/esr/regions")


def get_esr_units():
    """Returns a list of units of measure for ESR."""
    return make_request("/esr/unitsOfMeasure")


def get_esr_exports_all_countries(commodity_code, market_year):
    """Returns ESR exports data for a specific commodity globally."""
    return make_request(f"/esr/exports/commodityCode/{commodity_code}/allCountries/marketYear/{market_year}")


def get_esr_exports_country(commodity_code, country_code, market_year):
    """Returns ESR exports data for a specific commodity and country."""
    return make_request(
        f"/esr/exports/commodityCode/{commodity_code}/countryCode/{country_code}/marketYear/{market_year}")


def main():
    parser = argparse.ArgumentParser(description="Fetch data from the USDA FAS PSD Data API")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    subparsers.required = True

    # Setup subparsers for each endpoint
    subparsers.add_parser("attributes", help="Get commodity attributes")
    subparsers.add_parser("commodities", help="Get a list of commodities")
    subparsers.add_parser("countries", help="Get a list of countries")
    subparsers.add_parser("regions", help="Get a list of regions")
    subparsers.add_parser("units", help="Get a list of units of measure")

    world_parser = subparsers.add_parser("world-data", help="Get world data for a commodity")
    world_parser.add_argument("commodity_code", help="Commodity Code")
    world_parser.add_argument("market_year", help="Market Year (e.g., 2023)")

    country_parser = subparsers.add_parser("country-data", help="Get country data for a commodity")
    country_parser.add_argument("commodity_code", help="Commodity Code")
    country_parser.add_argument("country_code", help="Country Code")
    country_parser.add_argument("market_year", help="Market Year (e.g., 2023)")

    # ESR Subparsers
    subparsers.add_parser("esr-commodities", help="Get a list of ESR commodities")
    subparsers.add_parser("esr-countries", help="Get a list of ESR countries")
    subparsers.add_parser("esr-dates", help="Get a list of ESR data release dates")
    subparsers.add_parser("esr-regions", help="Get a list of ESR regions")
    subparsers.add_parser("esr-units", help="Get a list of ESR units of measure")

    esr_all_parser = subparsers.add_parser("esr-exports-all", help="Get ESR exports data globally")
    esr_all_parser.add_argument("commodity_code", help="Commodity Code")
    esr_all_parser.add_argument("market_year", help="Market Year")

    esr_country_parser = subparsers.add_parser("esr-exports-country", help="Get ESR exports data by country")
    esr_country_parser.add_argument("commodity_code", help="Commodity Code")
    esr_country_parser.add_argument("country_code", help="Country Code")
    esr_country_parser.add_argument("market_year", help="Market Year")

    args = parser.parse_args()

    # Dispatch based on command
    if args.command == "attributes":
        result = get_commodity_attributes()
    elif args.command == "commodities":
        result = get_commodities()
    elif args.command == "countries":
        result = get_countries()
    elif args.command == "regions":
        result = get_regions()
    elif args.command == "units":
        result = get_units_of_measure()
    elif args.command == "world-data":
        result = get_commodity_world_data(args.commodity_code, args.market_year)
    elif args.command == "country-data":
        result = get_commodity_country_data(args.commodity_code, args.country_code, args.market_year)
    elif args.command == "esr-commodities":
        result = get_esr_commodities()
    elif args.command == "esr-countries":
        result = get_esr_countries()
    elif args.command == "esr-dates":
        result = get_esr_datareleasedates()
    elif args.command == "esr-regions":
        result = get_esr_regions()
    elif args.command == "esr-units":
        result = get_esr_units()
    elif args.command == "esr-exports-all":
        result = get_esr_exports_all_countries(args.commodity_code, args.market_year)
    elif args.command == "esr-exports-country":
        result = get_esr_exports_country(args.commodity_code, args.country_code, args.market_year)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
