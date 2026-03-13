#!/usr/bin/env python3
"""CLI entry point for screen time tracker."""

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

from config import OUTPUT_DIR
from fetcher import discover_buckets, fetch_events
from timeline import build_timeline
from formatter import format_report


def generate_report(target_date):
    """Generate a screen time report for a specific date."""
    print(f"Generating report for {target_date}...")

    # Discover buckets
    window_bucket, afk_bucket, web_bucket = discover_buckets()
    if not window_bucket:
        print("ERROR: Could not find window watcher bucket. Is ActivityWatch running?")
        sys.exit(1)

    print(f"  Window: {window_bucket}")
    print(f"  AFK:    {afk_bucket or 'not found'}")
    print(f"  Web:    {web_bucket or 'not found'}")

    # Fetch events (strict midnight-to-midnight)
    window_events = fetch_events(window_bucket, target_date)
    afk_events = fetch_events(afk_bucket, target_date) if afk_bucket else []
    web_events = fetch_events(web_bucket, target_date) if web_bucket else []

    if not window_events:
        print(f"  No window events found for {target_date}. Skipping.")
        return None

    print(f"  Found {len(window_events)} window events, {len(afk_events)} AFK events, {len(web_events)} web events")

    # Build timeline
    timeline_data = build_timeline(window_events, afk_events, web_events)

    # Format report
    report = format_report(target_date, timeline_data)

    # Write to file
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{target_date.isoformat()} SCREENTIME.md"
    output_path = OUTPUT_DIR / filename
    output_path.write_text(report)
    print(f"  Written to {output_path}")

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generate screen time reports from ActivityWatch")
    parser.add_argument(
        "--date",
        type=str,
        help="Date to generate report for (YYYY-MM-DD). Defaults to yesterday.",
    )
    parser.add_argument(
        "--week",
        action="store_true",
        help="Generate reports for the past 7 days.",
    )
    parser.add_argument(
        "--today",
        action="store_true",
        help="Generate report for today (so far).",
    )

    args = parser.parse_args()

    if args.week:
        today = date.today()
        dates = [today - timedelta(days=i) for i in range(7, 0, -1)]
        for d in dates:
            generate_report(d)
        print("\nDone! Generated reports for the past 7 days.")
    elif args.date:
        target = date.fromisoformat(args.date)
        generate_report(target)
    elif args.today:
        generate_report(date.today())
    else:
        # Default: yesterday
        yesterday = date.today() - timedelta(days=1)
        generate_report(yesterday)


if __name__ == "__main__":
    main()
