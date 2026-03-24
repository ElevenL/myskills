#!/usr/bin/env python3
"""
USDA NASS Report Schedule Query Tool

Parse and query USDA report schedules from ICS calendar files.
"""

import argparse
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


def parse_ics_file(ics_path: Path) -> list[dict]:
    """Parse ICS file and extract events."""
    events = []

    with open(ics_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by VEVENT blocks
    vevent_pattern = r'BEGIN:VEVENT(.*?)END:VEVENT'
    matches = re.findall(vevent_pattern, content, re.DOTALL)

    for match in matches:
        event = {}

        # Extract SUMMARY
        summary_match = re.search(r'SUMMARY:(.+)', match)
        if summary_match:
            event['summary'] = summary_match.group(1).strip()

        # Extract DTSTART
        dtstart_match = re.search(r'DTSTART:(\d+)', match)
        if dtstart_match:
            dt_str = dtstart_match.group(1)
            if 'T' in dt_str or len(dt_str) > 8:
                event['dtstart'] = datetime.strptime(dt_str, '%Y%m%dT%H%M%S')
            else:
                event['dtstart'] = datetime.strptime(dt_str, '%Y%m%d')

        # Extract UID
        uid_match = re.search(r'UID:(.+)', match)
        if uid_match:
            event['uid'] = uid_match.group(1).strip()

        if event:
            events.append(event)

    return events


def get_report_type(summary: str) -> str:
    """Extract report type from summary."""
    if 'Prospective Plantings' in summary or '种植意向' in summary:
        return 'Prospective Plantings'
    elif 'Acreage' in summary or '种植面积' in summary:
        return 'Acreage'
    elif 'Grain Stocks' in summary or '季度库存' in summary:
        return 'Grain Stocks'
    elif 'Crop Production' in summary or '作物产量' in summary or '供需' in summary:
        return 'Crop Production'
    elif 'Crop Progress' in summary or '作物进展' in summary or '优良率' in summary:
        return 'Crop Progress'
    else:
        return 'Other'


def format_date(dt: datetime) -> str:
    """Format datetime for display."""
    weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    weekday = weekdays[dt.weekday()]
    return dt.strftime(f'%Y-%m-%d ({weekday})')


def list_all_reports(events: list[dict], report_type: Optional[str] = None,
                     start_date: Optional[datetime] = None,
                     end_date: Optional[datetime] = None) -> None:
    """List all reports, optionally filtered by type and date range."""
    filtered = events

    # Filter by report type
    if report_type:
        filtered = [e for e in filtered if get_report_type(e['summary']).lower() == report_type.lower()]

    # Filter by date range
    if start_date:
        filtered = [e for e in filtered if e['dtstart'] >= start_date]
    if end_date:
        filtered = [e for e in filtered if e['dtstart'] <= end_date]

    # Sort by date
    filtered.sort(key=lambda x: x['dtstart'])

    if not filtered:
        print("No reports found matching the criteria.")
        return

    print(f"\n{'Date':<22} {'Report Type':<22} {'Summary'}")
    print("-" * 80)

    for event in filtered:
        date_str = format_date(event['dtstart'])
        report_type_str = get_report_type(event['summary'])
        print(f"{date_str:<22} {report_type_str:<22} {event['summary']}")


def show_upcoming(events: list[dict], days: int = 30) -> None:
    """Show upcoming reports within specified days."""
    now = datetime.now()
    future = now + timedelta(days=days)

    upcoming = [e for e in events if now <= e['dtstart'] <= future]
    upcoming.sort(key=lambda x: x['dtstart'])

    if not upcoming:
        print(f"\nNo reports scheduled in the next {days} days.")
        return

    print(f"\n=== Upcoming USDA Reports (Next {days} Days) ===")
    print(f"{'Date':<22} {'Days Until':<12} {'Report Type':<22} {'Summary'}")
    print("-" * 90)

    for event in upcoming:
        days_until = (event['dtstart'] - now).days
        date_str = format_date(event['dtstart'])
        report_type_str = get_report_type(event['summary'])

        if days_until == 0:
            days_str = "TODAY"
        else:
            days_str = f"{days_until} days"

        print(f"{date_str:<22} {days_str:<12} {report_type_str:<22} {event['summary']}")


def show_report_types(events: list[dict]) -> None:
    """Show all available report types with counts."""
    type_counts = {}
    for event in events:
        rt = get_report_type(event['summary'])
        type_counts[rt] = type_counts.get(rt, 0) + 1

    print("\n=== Available Report Types ===")
    for rt, count in sorted(type_counts.items()):
        print(f"  {rt}: {count} reports")


def main():
    parser = argparse.ArgumentParser(
        description='Query USDA NASS report schedules',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show all reports
  python report_schedule.py list

  # Show upcoming reports in next 30 days
  python report_schedule.py upcoming

  # Show upcoming reports in next 7 days
  python report_schedule.py upcoming --days 7

  # Filter by report type
  python report_schedule.py list --type "Crop Production"
  python report_schedule.py list --type "Grain Stocks"

  # Filter by date range
  python report_schedule.py list --start 2026-04-01 --end 2026-06-30

  # Show available report types
  python report_schedule.py types
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # list command
    list_parser = subparsers.add_parser('list', help='List all reports')
    list_parser.add_argument('--type', '-t', help='Filter by report type')
    list_parser.add_argument('--start', '-s', help='Start date (YYYY-MM-DD)')
    list_parser.add_argument('--end', '-e', help='End date (YYYY-MM-DD)')

    # upcoming command
    upcoming_parser = subparsers.add_parser('upcoming', help='Show upcoming reports')
    upcoming_parser.add_argument('--days', '-d', type=int, default=30,
                                  help='Number of days to look ahead (default: 30)')

    # types command
    subparsers.add_parser('types', help='Show available report types')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Find ICS file
    script_dir = Path(__file__).parent
    ics_path = script_dir.parent / 'references' / 'NassReleases2026.ics'

    if not ics_path.exists():
        print(f"Error: ICS file not found at {ics_path}")
        return

    # Parse events
    events = parse_ics_file(ics_path)

    if args.command == 'list':
        start_date = None
        end_date = None

        if args.start:
            start_date = datetime.strptime(args.start, '%Y-%m-%d')
        if args.end:
            end_date = datetime.strptime(args.end, '%Y-%m-%d')

        list_all_reports(events, args.type, start_date, end_date)

    elif args.command == 'upcoming':
        show_upcoming(events, args.days)

    elif args.command == 'types':
        show_report_types(events)


if __name__ == '__main__':
    main()