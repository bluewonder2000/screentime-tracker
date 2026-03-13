"""Build timeline from raw ActivityWatch events."""

from datetime import timedelta
from categorizer import categorize
from config import (
    MERGE_GAP_SECONDS,
    FLOW_BLOCK_MIN_MINUTES,
    AFK_MIN_MINUTES,
    EXCLUDED_APPS,
)


def build_timeline(window_events, afk_events, web_events=None):
    """Merge window events into timeline blocks with AFK overlay.

    Args:
        window_events: List of window watcher events
        afk_events: List of AFK watcher events
        web_events: Optional list of web (Chrome) watcher events

    Returns:
        dict with keys: blocks, flow_blocks, afk_gaps, category_totals
    """
    # Filter out excluded apps
    excluded_lower = [x.lower() for x in EXCLUDED_APPS]
    window_events = [
        e for e in window_events
        if e["data"].get("app", "").lower() not in excluded_lower
    ]

    # Build AFK intervals
    afk_intervals = _build_afk_intervals(afk_events)

    # Enrich browser events with web titles
    if web_events:
        window_events = _enrich_with_web_titles(window_events, web_events)

    # Merge consecutive same-app events
    blocks = _merge_window_events(window_events)

    # Subtract AFK time from blocks
    blocks = _subtract_afk(blocks, afk_intervals)

    # Filter out tiny blocks (< 10 seconds active)
    blocks = [b for b in blocks if b["active_minutes"] >= 0.17]

    # Detect patterns
    flow_blocks = _detect_flow_blocks(blocks)
    afk_gaps = _build_afk_gaps(afk_events)

    # Calculate category totals
    category_totals = {}
    for block in blocks:
        cat = block["category"]
        category_totals[cat] = category_totals.get(cat, 0) + block["active_minutes"]

    return {
        "blocks": blocks,
        "flow_blocks": flow_blocks,
        "afk_gaps": afk_gaps,
        "category_totals": category_totals,
    }


def _enrich_with_web_titles(window_events, web_events):
    """Add web page title/URL to browser window events using web watcher data."""
    if not web_events:
        return window_events

    # Build a sorted list of web events for lookup
    web_sorted = sorted(web_events, key=lambda e: e["timestamp"])

    browser_apps = {"google chrome", "chrome", "arc", "safari", "firefox", "brave"}

    for event in window_events:
        app = event["data"].get("app", "").lower()
        if app not in browser_apps:
            continue

        # Find the closest web event at or before this window event's timestamp
        ts = event["timestamp"]
        best = None
        for we in web_sorted:
            if we["timestamp"] <= ts + timedelta(seconds=5):
                best = we
            else:
                break

        if best and abs((best["timestamp"] - ts).total_seconds()) < 30:
            event["data"]["web_url"] = best["data"].get("url", "")
            event["data"]["web_title"] = best["data"].get("title", "")

    return window_events


def _merge_window_events(events):
    """Merge consecutive events with the same app into blocks."""
    if not events:
        return []

    blocks = []
    current = None

    for event in events:
        app = event["data"].get("app", "Unknown")
        title = event["data"].get("title", "")
        web_title = event["data"].get("web_title", "")
        web_url = event["data"].get("web_url", "")
        start = event["timestamp"]
        duration = event["duration"]
        end = start + timedelta(seconds=duration)
        # Use web_title for categorization if available (better YouTube detection)
        cat_title = web_title or title
        category = categorize(app, cat_title)

        if current is None:
            current = {
                "app": app,
                "category": category,
                "start": start,
                "end": end,
                "duration_seconds": duration,
                "titles": [title] if title else [],
                "web_titles": [web_title] if web_title else [],
            }
            continue

        # Merge if same app and gap is small
        gap = (start - current["end"]).total_seconds()
        if app == current["app"] and gap <= MERGE_GAP_SECONDS:
            current["end"] = max(current["end"], end)
            current["duration_seconds"] += duration
            if title and title not in current["titles"]:
                current["titles"].append(title)
            if web_title and web_title not in current["web_titles"]:
                current["web_titles"].append(web_title)
        else:
            blocks.append(current)
            current = {
                "app": app,
                "category": category,
                "start": start,
                "end": end,
                "duration_seconds": duration,
                "titles": [title] if title else [],
                "web_titles": [web_title] if web_title else [],
            }

    if current:
        blocks.append(current)

    # Add active_minutes (before AFK subtraction, will be adjusted)
    for block in blocks:
        block["active_minutes"] = block["duration_seconds"] / 60

    return blocks


def _build_afk_intervals(afk_events):
    """Build list of (start, end) tuples where user was AFK."""
    intervals = []
    for event in afk_events:
        if event["data"].get("status") == "afk":
            start = event["timestamp"]
            end = start + timedelta(seconds=event["duration"])
            intervals.append((start, end))
    return intervals


def _subtract_afk(blocks, afk_intervals):
    """Subtract AFK time from block durations."""
    for block in blocks:
        afk_seconds = 0
        for afk_start, afk_end in afk_intervals:
            overlap_start = max(block["start"], afk_start)
            overlap_end = min(block["end"], afk_end)
            if overlap_start < overlap_end:
                afk_seconds += (overlap_end - overlap_start).total_seconds()

        active_seconds = max(0, block["duration_seconds"] - afk_seconds)
        block["active_minutes"] = active_seconds / 60

    return blocks


def _detect_flow_blocks(blocks):
    """Find blocks where user was in one app/category for 30+ min."""
    return [
        b for b in blocks
        if b["active_minutes"] >= FLOW_BLOCK_MIN_MINUTES
    ]


def _build_afk_gaps(afk_events):
    """Build list of significant AFK gaps, merging overlapping intervals."""
    raw = []
    for event in afk_events:
        if event["data"].get("status") == "afk":
            start = event["timestamp"]
            end = start + timedelta(seconds=event["duration"])
            raw.append((start, end))

    if not raw:
        return []

    # Sort and merge overlapping intervals
    raw.sort()
    merged = [raw[0]]
    for start, end in raw[1:]:
        if start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    # Filter by minimum duration
    min_duration = timedelta(minutes=AFK_MIN_MINUTES)
    gaps = []
    for start, end in merged:
        duration = end - start
        if duration >= min_duration:
            gaps.append({
                "start": start,
                "end": end,
                "duration_minutes": duration.total_seconds() / 60,
            })

    return gaps
