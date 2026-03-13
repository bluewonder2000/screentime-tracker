#!/usr/bin/env python3
"""CLI entry point for screen time tracker."""

import argparse
import logging
import sys
from datetime import date, timedelta
from pathlib import Path

from config import OUTPUT_DIR, DEVICES, WEEK_START_HOUR
from fetcher import fetch_all_devices
from timeline import build_timeline
from formatter import format_report
from weekly_formatter import format_weekly_report

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def fetch_and_build_timeline(target_date):
    """Fetch events from all devices and build a unified timeline.

    Args:
        target_date: datetime.date

    Returns:
        timeline_data dict, or None if no data available.
    """
    device_data = fetch_all_devices(DEVICES, target_date)
    if not device_data:
        return None

    all_window = []
    all_afk = []
    all_web = []
    for device_name, data in device_data.items():
        print(f"  {device_name}: {len(data['window_events'])} window, {len(data['afk_events'])} AFK, {len(data['web_events'])} web events")
        all_window.extend(data["window_events"])
        all_afk.extend(data["afk_events"])
        all_web.extend(data["web_events"])

    if not all_window:
        return None

    all_window.sort(key=lambda e: e["timestamp"])
    all_afk.sort(key=lambda e: e["timestamp"])
    all_web.sort(key=lambda e: e["timestamp"])

    return build_timeline(all_window, all_afk, all_web)


def generate_report(target_date):
    """Generate a screen time report for a specific date across all devices."""
    print(f"Generating report for {target_date}...")

    timeline_data = fetch_and_build_timeline(target_date)

    if not timeline_data:
        print(f"  No data for {target_date}. Skipping.")
        return None

    report = format_report(target_date, timeline_data)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{target_date.isoformat()} SCREENTIME.md"
    output_path = OUTPUT_DIR / filename
    output_path.write_text(report)
    print(f"  Written to {output_path}")

    return output_path


def get_week_range(reference_date):
    """Get the Sunday-to-Sunday range containing reference_date.

    Week runs Sunday noon to next Sunday noon. We fetch full days
    Sunday through Sunday (8 days) and let DAY_START_HOUR handle
    the noon boundary on each end.
    """
    days_since_sunday = (reference_date.weekday() + 1) % 7
    week_start = reference_date - timedelta(days=days_since_sunday)
    week_end = week_start + timedelta(days=7)  # Next Sunday
    return week_start, week_end


def generate_weekly_report(reference_date=None):
    """Generate a weekly summary report.

    The week runs Sunday noon to next Sunday noon. We temporarily
    override DAY_START_HOUR to WEEK_START_HOUR (noon) for the
    boundary Sundays, and use the normal DAY_START_HOUR for
    Mon-Sat (which fetches full days).
    """
    import config

    if reference_date is None:
        reference_date = date.today()

    week_start, week_end = get_week_range(reference_date)
    print(f"Generating weekly report for {week_start} → {week_end}...")

    original_day_start = config.DAY_START_HOUR
    days_data = {}

    try:
        for i in range(8):
            day = week_start + timedelta(days=i)
            is_boundary_sunday = (day == week_start or day == week_end)

            if is_boundary_sunday:
                config.DAY_START_HOUR = config.WEEK_START_HOUR
            else:
                config.DAY_START_HOUR = original_day_start

            print(f"  Fetching {day}...")
            timeline_data = fetch_and_build_timeline(day)

            if timeline_data:
                days_data[day] = timeline_data
    finally:
        config.DAY_START_HOUR = original_day_start

    if not days_data:
        print("No data available for any day this week.")
        return None

    report = format_weekly_report(week_start, week_end, days_data)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{week_start.isoformat()} WEEKLY.md"
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
        "--weekly",
        action="store_true",
        help="Generate weekly summary report.",
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

    if args.weekly:
        target = date.fromisoformat(args.date) if args.date else None
        generate_weekly_report(target)
    elif args.week:
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
        yesterday = date.today() - timedelta(days=1)
        generate_report(yesterday)


if __name__ == "__main__":
    main()
