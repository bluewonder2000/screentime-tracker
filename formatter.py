"""Generate Obsidian markdown from timeline data."""

from datetime import datetime
from config import CATEGORY_ORDER, TIMELINE_MIN_SECONDS

# Local timezone for display
_LOCAL_TZ = datetime.now().astimezone().tzinfo


def to_local(dt):
    """Convert a datetime to local time for display."""
    return dt.astimezone(_LOCAL_TZ)


def format_report(date, timeline_data):
    """Generate a markdown screen time report.

    Args:
        date: datetime.date
        timeline_data: dict from timeline.build_timeline()

    Returns:
        Markdown string
    """
    blocks = timeline_data["blocks"]
    flow_blocks = timeline_data["flow_blocks"]
    afk_gaps = timeline_data["afk_gaps"]
    totals = timeline_data["category_totals"]

    total_active = sum(totals.values())
    date_str = date.strftime("%Y-%m-%d")

    lines = []
    lines.append(f"## {date_str} SCREENTIME\n")

    # Summary line
    total_hrs = fmt_hours(total_active)
    afk_count = len(afk_gaps)
    flow_count = len(flow_blocks)
    lines.append(f"**Total:** {total_hrs} active | {afk_count} AFK gap{'s' if afk_count != 1 else ''} | {flow_count} flow block{'s' if flow_count != 1 else ''}\n")

    # By Category
    lines.append("### By Category")
    ordered_cats = sorted(
        totals.items(),
        key=lambda x: (CATEGORY_ORDER.index(x[0]) if x[0] in CATEGORY_ORDER else 99),
    )
    for cat, minutes in ordered_cats:
        pct = (minutes / total_active * 100) if total_active > 0 else 0
        lines.append(f"- {cat}: {fmt_hours(minutes)} ({pct:.0f}%)")
    lines.append("")

    # Flow Blocks
    if flow_blocks:
        lines.append("### Flow Blocks (30+ min uninterrupted)")
        for fb in flow_blocks:
            start = to_local(fb["start"]).strftime("%-I:%M%p").lower()
            end = to_local(fb["end"]).strftime("%-I:%M%p").lower()
            dur = fmt_duration(fb["active_minutes"])
            lines.append(f"- {start}–{end} — {fb['app']} ({fb['category']}) — {dur}")
        lines.append("")

    # AFK Gaps
    if afk_gaps:
        lines.append("### AFK Gaps")
        for gap in afk_gaps:
            start = to_local(gap["start"]).strftime("%-I:%M%p").lower()
            end = to_local(gap["end"]).strftime("%-I:%M%p").lower()
            dur = fmt_duration(gap["duration_minutes"])
            lines.append(f"- {start}–{end} ({dur})")
        lines.append("")

    # Timeline table (filter out very short blocks for readability)
    lines.append("### Timeline")
    lines.append("| Time | Device | App | Category | Duration | Detail |")
    lines.append("|------|--------|-----|----------|----------|--------|")
    for block in blocks:
        if block["active_minutes"] * 60 < TIMELINE_MIN_SECONDS:
            continue
        time_str = to_local(block["start"]).strftime("%-I:%M%p").lower()
        dur = fmt_duration(block["active_minutes"])
        detail = _get_detail(block)
        device = block.get("device", "")
        lines.append(f"| {time_str} | {device} | {block['app']} | {block['category']} | {dur} | {detail} |")
    lines.append("")

    return "\n".join(lines)


def _get_detail(block):
    """Get a short detail string for a timeline block (web title or window title)."""
    # Prefer web titles for browser blocks
    if block.get("web_titles"):
        # Show the most recent/primary title, truncated
        title = block["web_titles"][0]
        if len(block["web_titles"]) > 1:
            title += f" (+{len(block['web_titles']) - 1} more)"
        return _truncate(title, 60)

    # Fall back to window titles for non-browser apps
    if block.get("titles"):
        title = block["titles"][0]
        # Strip common suffixes like "— App Name"
        for sep in [" — ", " - ", " | "]:
            if sep in title:
                title = title.rsplit(sep, 1)[0]
        return _truncate(title, 60)

    return ""


def _truncate(text, max_len):
    """Truncate text with ellipsis."""
    if len(text) <= max_len:
        return text
    return text[:max_len - 1] + "…"


def fmt_hours(minutes):
    """Format minutes as 'X.Xhrs'."""
    hrs = minutes / 60
    if hrs < 0.1:
        return f"{minutes:.0f}min"
    return f"{hrs:.1f}hrs"


def fmt_duration(minutes):
    """Format minutes as 'Xh Ym' or 'Ym'."""
    if minutes < 1:
        return f"{minutes * 60:.0f}s"
    h = int(minutes // 60)
    m = int(minutes % 60)
    if h > 0:
        return f"{h}h {m}m"
    return f"{m}m"
