"""Tests for report formatter."""

from datetime import datetime, timezone, date


def _make_timeline_data():
    """Minimal timeline data for formatter tests."""
    block = {
        "app": "Cursor",
        "category": "Deep Work",
        "start": datetime(2026, 3, 11, 10, 0, tzinfo=timezone.utc),
        "end": datetime(2026, 3, 11, 10, 30, tzinfo=timezone.utc),
        "duration_seconds": 1800,
        "active_minutes": 30,
        "titles": ["main.py"],
        "web_titles": [],
        "device": "Mac",
    }
    return {
        "blocks": [block],
        "flow_blocks": [block],
        "afk_gaps": [],
        "category_totals": {"Deep Work": 30},
    }


def test_timeline_table_has_device_column():
    from formatter import format_report
    report = format_report(date(2026, 3, 11), _make_timeline_data())
    lines = report.split("\n")
    header_line = next(l for l in lines if l.startswith("| Time"))
    assert "Device" in header_line


def test_timeline_row_includes_device_name():
    from formatter import format_report
    report = format_report(date(2026, 3, 11), _make_timeline_data())
    assert "Mac" in report
