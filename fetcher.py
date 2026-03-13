"""Fetch events from ActivityWatch API."""

import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from config import AW_BASE_URL, WINDOW_BUCKET, AFK_BUCKET, WEB_BUCKET, DAY_START_HOUR


def _get_json(url):
    """Fetch JSON from a URL, following redirects."""
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def discover_buckets():
    """Auto-discover bucket names from the API."""
    buckets = _get_json(f"{AW_BASE_URL}/buckets")

    window = WINDOW_BUCKET
    afk = AFK_BUCKET
    web = WEB_BUCKET

    for name in buckets:
        if not window and name.startswith("aw-watcher-window"):
            window = name
        if not afk and name.startswith("aw-watcher-afk"):
            afk = name
        # Prefer the hostname-suffixed bucket (actively tracking)
        if name.startswith("aw-watcher-web-chrome") and ("." in name.split("aw-watcher-web-chrome")[-1]):
            web = name
        elif not web and name.startswith("aw-watcher-web-chrome"):
            web = name

    return window, afk, web


def fetch_events(bucket_id, date):
    """Fetch events for a specific bucket and date.

    Args:
        bucket_id: ActivityWatch bucket ID
        date: datetime.date object

    Returns:
        List of event dicts with 'timestamp', 'duration', and 'data' keys.
    """
    # Build time range using DAY_START_HOUR boundary (e.g. 5am to 5am)
    local_tz = datetime.now().astimezone().tzinfo
    start = datetime(date.year, date.month, date.day, hour=DAY_START_HOUR, tzinfo=local_tz)
    end = start + timedelta(days=1)

    params = urllib.parse.urlencode({
        "start": start.isoformat(),
        "end": end.isoformat(),
    })

    url = f"{AW_BASE_URL}/buckets/{bucket_id}/events?{params}"
    events = _get_json(url)

    # Parse timestamps and normalize
    for event in events:
        event["timestamp"] = datetime.fromisoformat(event["timestamp"])
        event["duration"] = float(event.get("duration", 0))

    # Sort chronologically
    events.sort(key=lambda e: e["timestamp"])

    return events
