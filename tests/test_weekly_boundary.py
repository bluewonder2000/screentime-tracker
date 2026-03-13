"""Tests for weekly report boundary calculations."""

from datetime import date


def test_get_week_range_from_thursday():
    """A Thursday should produce the preceding Sunday as week start."""
    from run import get_week_range
    start, end = get_week_range(date(2026, 3, 12))
    assert start.weekday() == 6  # Sunday
    assert end.weekday() == 6    # Next Sunday
    assert start == date(2026, 3, 8)
    assert end == date(2026, 3, 15)


def test_get_week_range_from_sunday():
    """A Sunday should use itself as the week start."""
    from run import get_week_range
    start, end = get_week_range(date(2026, 3, 8))
    assert start == date(2026, 3, 8)
    assert end == date(2026, 3, 15)
