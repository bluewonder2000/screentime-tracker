"""Parse iPhone Screen Time data from macOS Biome App.InFocus SEGB files."""

import logging
import struct
from datetime import datetime, timedelta, timezone

from config import (
    BUNDLE_ID_MAP,
    IPHONE_BIOME_PATH,
    IPHONE_EXCLUDED_APPS,
    IPHONE_SESSION_CAP_SECONDS,
    DAY_START_HOUR,
)

logger = logging.getLogger(__name__)

# Apple epoch: 2001-01-01 00:00:00 UTC
APPLE_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)

# SEGB record header pattern bytes
RECORD_HEADER = bytes([0x10, 0x01, 0x18])


def _resolve_app_name(bundle_id):
    """Resolve a bundle ID to a human-readable app name."""
    if bundle_id in BUNDLE_ID_MAP:
        return BUNDLE_ID_MAP[bundle_id]
    # Fallback: last segment, title-cased
    last = bundle_id.rsplit(".", 1)[-1]
    return last.title()


def parse_segb_files(biome_dir, target_date):
    """Read all SEGB files in biome_dir and extract App.InFocus records.

    Returns list of (timestamp, flag, bundle_id) tuples sorted by timestamp.
    flag: 0 = app started focus, 1 = app ended focus.
    """
    records = []
    local_tz = datetime.now().astimezone().tzinfo
    day_start = datetime(target_date.year, target_date.month, target_date.day,
                         hour=DAY_START_HOUR, tzinfo=local_tz)
    day_end = day_start + timedelta(days=1)

    for path in sorted(biome_dir.iterdir()):
        if not path.is_file() or not path.name.isdigit():
            continue
        data = path.read_bytes()
        _parse_segb_data(data, records, day_start, day_end)

    records.sort(key=lambda r: r[0])
    return records


def _parse_segb_data(data, records, day_start, day_end):
    """Scan binary data for App.InFocus record patterns."""
    i = 0
    while i < len(data) - 20:
        # Look for record header: 10 01 18 [flag] 21 [timestamp] 32 [len] [bundle_id]
        if data[i:i + 3] != RECORD_HEADER:
            i += 1
            continue

        flag = data[i + 3]
        if flag not in (0x00, 0x01):
            i += 1
            continue

        if i + 4 >= len(data) or data[i + 4] != 0x21:
            i += 1
            continue

        if i + 13 >= len(data):
            i += 1
            continue

        # 8-byte little-endian double timestamp
        ts_bytes = data[i + 5:i + 13]
        try:
            ts_val = struct.unpack("<d", ts_bytes)[0]
        except struct.error:
            i += 1
            continue

        # Sanity check: Apple epoch seconds should be roughly 700M-900M for 2023-2030
        if not (700_000_000 < ts_val < 900_000_000):
            i += 1
            continue

        timestamp = APPLE_EPOCH + timedelta(seconds=ts_val)
        timestamp = timestamp.astimezone(day_start.tzinfo)

        # Check for bundle ID marker: 0x32 [length] [string]
        pos = i + 13
        if pos >= len(data) or data[pos] != 0x32:
            i += 1
            continue
        pos += 1

        if pos >= len(data):
            i += 1
            continue
        str_len = data[pos]
        pos += 1

        if pos + str_len > len(data):
            i += 1
            continue

        try:
            bundle_id = data[pos:pos + str_len].decode("utf-8")
        except UnicodeDecodeError:
            i += 1
            continue

        # Filter to target date
        if day_start <= timestamp < day_end:
            records.append((timestamp, flag, bundle_id))

        i = pos + str_len

    return records


def _compute_events(records, session_cap):
    """Convert raw records into duration-based events.

    Uses END events (flag=1) as foreground markers: when an END fires,
    that app was in the foreground. Duration = time from one END to the next END,
    capped at session_cap seconds.
    """
    events = []
    # Filter to END events only
    end_events = [(ts, bid) for ts, flag, bid in records if flag == 1]

    for idx in range(len(end_events) - 1):
        ts, bundle_id = end_events[idx]
        next_ts = end_events[idx + 1][0]

        duration = (next_ts - ts).total_seconds()
        if duration <= 0:
            continue
        duration = min(duration, session_cap)

        events.append({
            "timestamp": ts,
            "duration": duration,
            "device": "iPhone",
            "data": {
                "app": _resolve_app_name(bundle_id),
                "title": "",
            },
        })

    return events


def fetch_iphone_events(target_date):
    """Fetch iPhone screen time events from Biome App.InFocus data.

    Returns dict with window_events/afk_events/web_events matching
    the format from fetcher.py, or None if Biome path doesn't exist.
    """
    if not IPHONE_BIOME_PATH.exists():
        logger.info("iPhone Biome path not found, skipping iPhone data.")
        return None

    records = parse_segb_files(IPHONE_BIOME_PATH, target_date)
    if not records:
        logger.info(f"No iPhone records found for {target_date}.")
        return None

    # Filter excluded apps before computing events
    records = [(ts, flag, bid) for ts, flag, bid in records
               if bid not in IPHONE_EXCLUDED_APPS]

    events = _compute_events(records, IPHONE_SESSION_CAP_SECONDS)

    if not events:
        return None

    return {
        "window_events": events,
        "afk_events": [],
        "web_events": [],
    }
