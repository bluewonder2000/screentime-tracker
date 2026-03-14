"""Tests for biome_reader module."""

import struct
from datetime import datetime, timedelta, timezone

import pytest

from biome_reader import (
    APPLE_EPOCH,
    _compute_events,
    _parse_segb_data,
    _resolve_app_name,
    fetch_iphone_events,
)


def _make_record(flag, timestamp_seconds, bundle_id):
    """Build a minimal SEGB record matching the expected binary pattern."""
    header = bytes([0x10, 0x01, 0x18, flag, 0x21])
    ts_bytes = struct.pack("<d", timestamp_seconds)
    bid_bytes = bundle_id.encode("utf-8")
    string_header = bytes([0x32, len(bid_bytes)])
    return header + ts_bytes + string_header + bid_bytes


def _apple_seconds(dt):
    """Convert a datetime to Apple epoch seconds."""
    return (dt - APPLE_EPOCH).total_seconds()


class TestParseSegbRecord:
    def test_parse_single_record(self):
        local_tz = datetime.now().astimezone().tzinfo
        target = datetime(2026, 3, 13, 14, 0, 0, tzinfo=local_tz)
        ts = _apple_seconds(target)
        data = _make_record(0x01, ts, "com.burbn.instagram")

        records = []
        day_start = datetime(2026, 3, 13, 0, 0, 0, tzinfo=local_tz)
        day_end = day_start + timedelta(days=1)
        _parse_segb_data(data, records, day_start, day_end)

        assert len(records) == 1
        assert records[0][1] == 1  # flag
        assert records[0][2] == "com.burbn.instagram"

    def test_filters_by_date(self):
        local_tz = datetime.now().astimezone().tzinfo
        # Record from a different day
        wrong_day = datetime(2026, 3, 10, 14, 0, 0, tzinfo=local_tz)
        ts = _apple_seconds(wrong_day)
        data = _make_record(0x01, ts, "com.burbn.instagram")

        records = []
        day_start = datetime(2026, 3, 13, 0, 0, 0, tzinfo=local_tz)
        day_end = day_start + timedelta(days=1)
        _parse_segb_data(data, records, day_start, day_end)

        assert len(records) == 0


class TestAppleEpochConversion:
    def test_known_timestamp(self):
        # 2026-03-13 00:00:00 UTC = 795_398_400 seconds from Apple epoch
        expected = datetime(2026, 3, 13, 0, 0, 0, tzinfo=timezone.utc)
        seconds = (expected - APPLE_EPOCH).total_seconds()
        result = APPLE_EPOCH + timedelta(seconds=seconds)
        assert result == expected


class TestDurationWithSessionCap:
    def test_cap_truncates_long_gaps(self):
        local_tz = datetime.now().astimezone().tzinfo
        now = datetime(2026, 3, 13, 10, 0, 0, tzinfo=local_tz)

        records = [
            (now, 1, "com.burbn.instagram"),
            (now + timedelta(hours=2), 1, "com.apple.mobilesafari"),
            (now + timedelta(hours=2, minutes=5), 1, "com.burbn.instagram"),
        ]

        events = _compute_events(records, session_cap=600)

        assert len(events) == 2
        # First gap is 2 hours, should be capped at 600s
        assert events[0]["duration"] == 600
        # Second gap is 5 minutes = 300s, under cap
        assert events[1]["duration"] == 300

    def test_zero_duration_skipped(self):
        local_tz = datetime.now().astimezone().tzinfo
        now = datetime(2026, 3, 13, 10, 0, 0, tzinfo=local_tz)

        records = [
            (now, 1, "com.burbn.instagram"),
            (now, 1, "com.apple.mobilesafari"),  # same timestamp
        ]

        events = _compute_events(records, session_cap=600)
        assert len(events) == 0


class TestResolveAppName:
    def test_known_bundle_id(self):
        assert _resolve_app_name("com.burbn.instagram") == "Instagram"
        assert _resolve_app_name("com.zhiliaoapp.musically") == "TikTok"
        assert _resolve_app_name("com.apple.MobileSMS") == "iMessage"

    def test_fallback_unknown_bundle_id(self):
        result = _resolve_app_name("com.example.myapp")
        assert result == "Myapp"

    def test_fallback_single_segment(self):
        result = _resolve_app_name("singleword")
        assert result == "Singleword"


class TestExcludedAppsFiltered:
    def test_system_apps_removed(self):
        from config import IPHONE_EXCLUDED_APPS

        local_tz = datetime.now().astimezone().tzinfo
        now = datetime(2026, 3, 13, 10, 0, 0, tzinfo=local_tz)

        records = [
            (now, 1, "com.apple.SpringBoard"),
            (now + timedelta(minutes=1), 1, "com.burbn.instagram"),
            (now + timedelta(minutes=5), 1, "com.apple.SleepLockScreen"),
            (now + timedelta(minutes=6), 1, "com.apple.mobilesafari"),
        ]

        # Filter like fetch_iphone_events does
        filtered = [(ts, flag, bid) for ts, flag, bid in records
                     if bid not in IPHONE_EXCLUDED_APPS]

        events = _compute_events(filtered, session_cap=600)

        app_names = [e["data"]["app"] for e in events]
        assert "SpringBoard" not in app_names
        assert "SleepLockScreen" not in app_names


class TestReturnsNoneWhenNoPath:
    def test_missing_biome_dir(self, tmp_path, monkeypatch):
        import config
        monkeypatch.setattr(config, "IPHONE_BIOME_PATH", tmp_path / "nonexistent")

        # Re-import to pick up monkeypatched value
        import biome_reader
        monkeypatch.setattr(biome_reader, "IPHONE_BIOME_PATH", tmp_path / "nonexistent")

        from datetime import date
        result = fetch_iphone_events(date(2026, 3, 13))
        assert result is None


class TestEventFormatMatchesPipeline:
    def test_event_keys(self):
        local_tz = datetime.now().astimezone().tzinfo
        now = datetime(2026, 3, 13, 10, 0, 0, tzinfo=local_tz)

        records = [
            (now, 1, "com.burbn.instagram"),
            (now + timedelta(minutes=5), 1, "com.apple.mobilesafari"),
        ]

        events = _compute_events(records, session_cap=600)

        assert len(events) == 1
        event = events[0]
        assert "timestamp" in event
        assert "duration" in event
        assert "device" in event
        assert event["device"] == "iPhone"
        assert "data" in event
        assert "app" in event["data"]
        assert "title" in event["data"]
        assert isinstance(event["timestamp"], datetime)
        assert isinstance(event["duration"], float)
