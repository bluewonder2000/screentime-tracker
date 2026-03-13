"""Tests for multi-device timeline building."""

from datetime import datetime, timezone, timedelta


def _make_event(app, ts_offset_min=0, duration_sec=300, device="Mac", title="", web_title=""):
    """Helper to build a fake window event."""
    base = datetime(2026, 3, 11, 10, 0, tzinfo=timezone.utc) + timedelta(minutes=ts_offset_min)
    event = {
        "timestamp": base,
        "duration": duration_sec,
        "device": device,
        "data": {"app": app, "title": title},
    }
    if web_title:
        event["data"]["web_title"] = web_title
    return event


def _make_afk(ts_offset_min=0, duration_sec=600, device="Mac"):
    base = datetime(2026, 3, 11, 10, 0, tzinfo=timezone.utc) + timedelta(minutes=ts_offset_min)
    return {
        "timestamp": base,
        "duration": duration_sec,
        "device": device,
        "data": {"status": "afk"},
    }


def test_build_timeline_merges_multi_device_events():
    """Events from multiple devices should merge into a single timeline, sorted by time."""
    from timeline import build_timeline

    mac_events = [_make_event("Cursor", ts_offset_min=0, device="Mac")]
    win_events = [_make_event("Code", ts_offset_min=2, device="Windows")]

    all_window = mac_events + win_events
    result = build_timeline(all_window, [])

    apps = [b["app"] for b in result["blocks"]]
    assert "Cursor" in apps
    assert "Code" in apps


def test_build_timeline_preserves_device_tag():
    """Each block should carry the device name from its events."""
    from timeline import build_timeline

    events = [_make_event("Cursor", device="Mac")]
    result = build_timeline(events, [])
    assert result["blocks"][0]["device"] == "Mac"


def test_afk_subtracted_per_device():
    """AFK on Mac should not subtract time from Windows blocks."""
    from timeline import build_timeline

    mac_event = _make_event("Cursor", ts_offset_min=0, duration_sec=600, device="Mac")
    win_event = _make_event("Code", ts_offset_min=0, duration_sec=600, device="Windows")
    mac_afk = _make_afk(ts_offset_min=0, duration_sec=600, device="Mac")

    result = build_timeline([mac_event, win_event], [mac_afk])

    blocks_by_device = {b["app"]: b for b in result["blocks"]}
    # Mac Cursor should have ~0 active time (fully AFK)
    assert blocks_by_device["Cursor"]["active_minutes"] < 1
    # Windows Code should be unaffected
    assert blocks_by_device["Code"]["active_minutes"] >= 9
