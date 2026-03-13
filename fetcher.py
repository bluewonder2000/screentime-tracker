"""Fetch events from ActivityWatch API across multiple devices."""

import json
import logging
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from config import DAY_START_HOUR

logger = logging.getLogger(__name__)


def _get_json(url):
    """Fetch JSON from a URL, following redirects."""
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def discover_buckets_for_device(device):
    """Auto-discover bucket names from a single device's API.

    Args:
        device: dict with 'name' and 'url' keys

    Returns:
        (window_bucket, afk_bucket, web_bucket) — any may be None
    """
    base_url = device["url"]
    buckets = _get_json(f"{base_url}/buckets")

    window = None
    afk = None
    web = None

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


def fetch_events(bucket_id, target_date, device):
    """Fetch events for a specific bucket and date from a device.

    Args:
        bucket_id: ActivityWatch bucket ID
        target_date: datetime.date object
        device: dict with 'name' and 'url' keys

    Returns:
        List of event dicts tagged with device name.
    """
    base_url = device["url"]
    local_tz = datetime.now().astimezone().tzinfo
    start = datetime(target_date.year, target_date.month, target_date.day, hour=DAY_START_HOUR, tzinfo=local_tz)
    end = start + timedelta(days=1)

    params = urllib.parse.urlencode({
        "start": start.isoformat(),
        "end": end.isoformat(),
    })

    url = f"{base_url}/buckets/{bucket_id}/events?{params}"
    events = _get_json(url)

    for event in events:
        event["timestamp"] = datetime.fromisoformat(event["timestamp"])
        event["duration"] = float(event.get("duration", 0))
        event["device"] = device["name"]

    events.sort(key=lambda e: e["timestamp"])
    return events


def fetch_all_devices(devices, target_date):
    """Fetch events from all devices for a given date.

    Args:
        devices: list of device dicts (each has 'name' and 'url')
        target_date: datetime.date

    Returns:
        dict keyed by device name, each value is a dict with:
            window_events, afk_events, web_events
        Unreachable devices are skipped with a warning.
    """
    results = {}

    for device in devices:
        try:
            window_bucket, afk_bucket, web_bucket = discover_buckets_for_device(device)
        except Exception as e:
            logger.warning(f"Device '{device['name']}' unreachable: {e}")
            continue

        if not window_bucket:
            logger.warning(f"Device '{device['name']}': no window bucket found, skipping.")
            continue

        try:
            window_events = fetch_events(window_bucket, target_date, device)
            afk_events = fetch_events(afk_bucket, target_date, device) if afk_bucket else []
            web_events = fetch_events(web_bucket, target_date, device) if web_bucket else []
        except Exception as e:
            logger.warning(f"Device '{device['name']}' fetch failed: {e}")
            continue

        results[device["name"]] = {
            "window_events": window_events,
            "afk_events": afk_events,
            "web_events": web_events,
        }

    return results
