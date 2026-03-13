"""Tests for configuration."""


def test_devices_list_exists():
    from config import DEVICES
    assert isinstance(DEVICES, list)
    assert len(DEVICES) >= 1


def test_device_has_name_and_url():
    from config import DEVICES
    for device in DEVICES:
        assert "name" in device
        assert "url" in device
        assert device["url"].startswith("http")


def test_week_start_hour_exists():
    from config import WEEK_START_HOUR
    assert isinstance(WEEK_START_HOUR, int)
    assert 0 <= WEEK_START_HOUR <= 23


def test_old_single_device_config_removed():
    """AW_BASE_URL and global bucket overrides should no longer exist."""
    import config
    assert not hasattr(config, "AW_BASE_URL")
    assert not hasattr(config, "WINDOW_BUCKET")
    assert not hasattr(config, "AFK_BUCKET")
    assert not hasattr(config, "WEB_BUCKET")
