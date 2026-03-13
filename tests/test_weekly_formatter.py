"""Tests for weekly report formatter."""

from datetime import datetime, timezone, date, timedelta


def _make_block(app, category, start_offset_hrs=0, duration_min=30, device="Mac"):
    base = datetime(2026, 3, 11, 10, 0, tzinfo=timezone.utc)
    start = base + timedelta(hours=start_offset_hrs)
    end = start + timedelta(minutes=duration_min)
    return {
        "app": app, "category": category, "start": start, "end": end,
        "duration_seconds": duration_min * 60, "active_minutes": duration_min,
        "titles": [], "web_titles": [], "device": device,
    }


def _make_day_data(blocks=None, flow_blocks=None, afk_gaps=None, totals=None):
    return {
        "blocks": blocks or [], "flow_blocks": flow_blocks or [],
        "afk_gaps": afk_gaps or [], "category_totals": totals or {},
    }


def test_aggregate_total_hours():
    from weekly_formatter import _aggregate_weekly_stats
    cursor_block = _make_block("Cursor", "Deep Work", duration_min=120)
    day1 = _make_day_data(blocks=[cursor_block], flow_blocks=[cursor_block], totals={"Deep Work": 120})
    day2 = _make_day_data(blocks=[_make_block("Chrome", "Browsing", duration_min=60)], totals={"Browsing": 60})
    stats = _aggregate_weekly_stats({date(2026, 3, 11): day1, date(2026, 3, 12): day2})
    assert stats["total_minutes"] == 180
    assert stats["day_count"] == 2


def test_top_apps_ranked_by_time():
    from weekly_formatter import _aggregate_weekly_stats
    blocks = [
        _make_block("Cursor", "Deep Work", duration_min=120),
        _make_block("Chrome", "Browsing", start_offset_hrs=3, duration_min=60),
    ]
    day = _make_day_data(blocks=blocks, totals={"Deep Work": 120, "Browsing": 60})
    stats = _aggregate_weekly_stats({date(2026, 3, 11): day})
    assert stats["top_apps"][0][0] == "Cursor"
    assert stats["top_apps"][1][0] == "Chrome"


def test_peak_work_hours_groups_into_windows():
    from weekly_formatter import _aggregate_weekly_stats
    blocks = [
        _make_block("Cursor", "Deep Work", start_offset_hrs=13, duration_min=60),  # 11pm
        _make_block("Cursor", "Deep Work", start_offset_hrs=14, duration_min=60),  # 12am
        _make_block("Cursor", "Deep Work", start_offset_hrs=15, duration_min=60),  # 1am
    ]
    day = _make_day_data(blocks=blocks, totals={"Deep Work": 180})
    stats = _aggregate_weekly_stats({date(2026, 3, 11): day})
    peak = stats["peak_windows"][0]
    assert peak["total_minutes"] == 180
    assert peak["start_hour"] == 23
    assert peak["end_hour"] == 2


def test_format_weekly_report_header():
    from weekly_formatter import format_weekly_report
    day = _make_day_data(blocks=[_make_block("Cursor", "Deep Work", duration_min=60)], totals={"Deep Work": 60})
    report = format_weekly_report(date(2026, 3, 8), date(2026, 3, 14), {date(2026, 3, 11): day})
    assert "WEEKLY SCREENTIME" in report
    assert "2026-03-08" in report


def test_daily_breakdown_table():
    from weekly_formatter import format_weekly_report
    day = _make_day_data(
        blocks=[_make_block("Cursor", "Deep Work", duration_min=60)],
        flow_blocks=[_make_block("Cursor", "Deep Work", duration_min=60)],
        totals={"Deep Work": 60},
    )
    report = format_weekly_report(date(2026, 3, 8), date(2026, 3, 14), {date(2026, 3, 11): day})
    assert "Daily Breakdown" in report
    assert "Wed" in report
