"""Tests for multi-device fetcher."""

from unittest.mock import patch, MagicMock
from datetime import date


def _make_device(name="Mac", url="http://localhost:5600/api/0"):
    return {"name": name, "url": url}


def test_discover_buckets_for_device_returns_tuple():
    """discover_buckets_for_device should return (window, afk, web) bucket names."""
    from fetcher import discover_buckets_for_device

    fake_buckets = {
        "aw-watcher-window_mac": {},
        "aw-watcher-afk_mac": {},
        "aw-watcher-web-chrome_mac.local": {},
    }
    with patch("fetcher._get_json", return_value=fake_buckets):
        device = _make_device()
        w, a, web = discover_buckets_for_device(device)
        assert w == "aw-watcher-window_mac"
        assert a == "aw-watcher-afk_mac"
        assert "web-chrome" in web


def test_fetch_events_tags_device_name():
    """Events should have a 'device' key added."""
    from fetcher import fetch_events

    fake_events = [
        {"timestamp": "2026-03-11T10:00:00-07:00", "duration": 60, "data": {"app": "Cursor"}}
    ]
    device = _make_device("Mac")
    with patch("fetcher._get_json", return_value=fake_events):
        events = fetch_events("aw-watcher-window_mac", date(2026, 3, 11), device)
        assert events[0]["device"] == "Mac"


def test_fetch_all_devices_skips_unreachable():
    """If a device is unreachable, skip it and continue."""
    from fetcher import fetch_all_devices

    devices = [_make_device("Mac"), _make_device("Windows", "http://10.0.0.1:5600/api/0")]

    def mock_discover(device):
        if device["name"] == "Windows":
            raise ConnectionError("unreachable")
        return ("aw-watcher-window_mac", "aw-watcher-afk_mac", None)

    def mock_fetch(bucket, dt, device):
        return [{"timestamp": "2026-03-11T10:00:00-07:00", "duration": 60,
                 "data": {"app": "Cursor"}, "device": "Mac"}]

    with patch("fetcher.discover_buckets_for_device", side_effect=mock_discover), \
         patch("fetcher.fetch_events", side_effect=mock_fetch):
        result = fetch_all_devices(devices, date(2026, 3, 11))
        # Should have data from Mac only, no crash
        assert result["Mac"]["window_events"] is not None
        assert "Windows" not in result
