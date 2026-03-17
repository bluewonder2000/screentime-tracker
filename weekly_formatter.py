"""Weekly report aggregation and formatting."""

from datetime import datetime
from collections import defaultdict
from urllib.parse import urlparse
from formatter import fmt_hours, fmt_duration, to_local

BROWSER_APPS = {"arc", "google chrome", "chrome", "safari", "firefox", "brave", "arc.exe"}


DOMAIN_LABELS = {
    "docs.google.com": "Google Docs",
    "mail.google.com": "Gmail",
    "drive.google.com": "Google Drive",
    "sheets.google.com": "Google Sheets",
    "slides.google.com": "Google Slides",
    "calendar.google.com": "Google Calendar",
    "meet.google.com": "Google Meet",
    "google.com": "Google Search",
    "youtube.com": "YouTube",
    "github.com": "GitHub",
    "reddit.com": "Reddit",
    "twitter.com": "X (Twitter)",
    "x.com": "X (Twitter)",
    "instagram.com": "Instagram",
    "facebook.com": "Facebook",
    "linkedin.com": "LinkedIn",
    "notion.so": "Notion",
    "figma.com": "Figma",
    "slack.com": "Slack",
    "discord.com": "Discord",
    "stackoverflow.com": "Stack Overflow",
    "amazon.com": "Amazon",
    "netflix.com": "Netflix",
    "twitch.tv": "Twitch",
    "spotify.com": "Spotify Web",
    "chat.openai.com": "ChatGPT",
    "chatgpt.com": "ChatGPT",
    "claude.ai": "Claude",
    "medium.com": "Medium",
    "wikipedia.org": "Wikipedia",
    "tiktok.com": "TikTok",
    "pinterest.com": "Pinterest",
    "canva.com": "Canva",
    "vercel.com": "Vercel",
    "netlify.com": "Netlify",
    "linear.app": "Linear",
    "todoist.com": "Todoist",
    "bitwarden.com": "Bitwarden",
}


def _domain_from_url(url):
    """Extract a readable site name from a URL."""
    try:
        host = urlparse(url).hostname or ""
    except Exception:
        return None
    if not host:
        return None
    if host.startswith("www."):
        host = host[4:]
    # Check exact match first, then try without subdomain
    if host in DOMAIN_LABELS:
        return DOMAIN_LABELS[host]
    # Try base domain (e.g. 'en.wikipedia.org' -> 'wikipedia.org')
    parts = host.split(".")
    if len(parts) > 2:
        base = ".".join(parts[-2:])
        if base in DOMAIN_LABELS:
            return DOMAIN_LABELS[base]
    # Fallback: capitalize the second-level domain
    if len(parts) >= 2:
        return parts[-2].capitalize()
    return host


def _build_peak_windows(deep_work_by_hour):
    """Group consecutive hours of deep work into multi-hour windows.
    Handles midnight wraparound (e.g., hours 22,23,0,1 -> one window 10pm-2am).
    """
    if not deep_work_by_hour:
        return []
    hours_sorted = sorted(deep_work_by_hour.keys())
    windows = []
    current_start = hours_sorted[0]
    current_end = hours_sorted[0]
    current_total = deep_work_by_hour[current_start]
    for hour in hours_sorted[1:]:
        if hour == current_end + 1:
            current_end = hour
            current_total += deep_work_by_hour[hour]
        else:
            windows.append({"start_hour": current_start, "end_hour": (current_end + 1) % 24, "total_minutes": current_total})
            current_start = hour
            current_end = hour
            current_total = deep_work_by_hour[hour]
    windows.append({"start_hour": current_start, "end_hour": (current_end + 1) % 24, "total_minutes": current_total})
    # Merge first and last windows if they wrap around midnight
    if len(windows) >= 2 and windows[-1]["end_hour"] == windows[0]["start_hour"]:
        merged = {"start_hour": windows[-1]["start_hour"], "end_hour": windows[0]["end_hour"], "total_minutes": windows[-1]["total_minutes"] + windows[0]["total_minutes"]}
        windows = [merged] + windows[1:-1]
    windows.sort(key=lambda w: w["total_minutes"], reverse=True)
    return windows


def _aggregate_weekly_stats(days_data):
    """Aggregate timeline data across multiple days."""
    total_minutes = 0
    app_minutes = defaultdict(float)
    device_minutes = defaultdict(float)
    deep_work_by_hour = defaultdict(float)
    all_flow_blocks = []
    all_afk_gaps = []
    category_totals = defaultdict(float)
    daily_summaries = []
    for day_date, data in sorted(days_data.items()):
        day_total = sum(data["category_totals"].values())
        total_minutes += day_total
        for cat, mins in data["category_totals"].items():
            category_totals[cat] += mins
        for block in data["blocks"]:
            device_minutes[block.get("device", "Unknown")] += block["active_minutes"]
            # For browser apps, attribute time to domains instead
            if block["app"].lower() in BROWSER_APPS and block.get("web_urls"):
                urls = block["web_urls"]
                per_url_minutes = block["active_minutes"] / len(urls) if urls else 0
                for url in urls:
                    domain = _domain_from_url(url)
                    if domain:
                        app_minutes[domain] += per_url_minutes
                    else:
                        app_minutes[block["app"]] += per_url_minutes
            else:
                app_minutes[block["app"]] += block["active_minutes"]
            if block["category"] == "Deep Work":
                hour = block["start"].hour
                deep_work_by_hour[hour] += block["active_minutes"]
        all_flow_blocks.extend(data["flow_blocks"])
        all_afk_gaps.extend(data["afk_gaps"])
        first_block = data["blocks"][0] if data["blocks"] else None
        last_block = data["blocks"][-1] if data["blocks"] else None
        # Compute top app using domain-resolved names for browsers
        day_app_minutes = defaultdict(float)
        for block in data["blocks"]:
            if block["app"].lower() in BROWSER_APPS and block.get("web_urls"):
                urls = block["web_urls"]
                per_url = block["active_minutes"] / len(urls) if urls else 0
                for url in urls:
                    domain = _domain_from_url(url)
                    day_app_minutes[domain or block["app"]] += per_url
            else:
                day_app_minutes[block["app"]] += block["active_minutes"]
        top_app = max(day_app_minutes.items(), key=lambda x: x[1], default=("—", 0))
        daily_summaries.append({
            "date": day_date, "total_minutes": day_total,
            "start": to_local(first_block["start"]) if first_block else None,
            "end": to_local(last_block["end"]) if last_block else None,
            "flow_count": len(data["flow_blocks"]), "top_app": top_app[0],
        })
    top_apps = sorted(app_minutes.items(), key=lambda x: x[1], reverse=True)
    peak_windows = _build_peak_windows(dict(deep_work_by_hour))
    flow_app_counts = defaultdict(int)
    longest_flow = None
    for fb in all_flow_blocks:
        flow_app_counts[fb["app"]] += 1
        if longest_flow is None or fb["active_minutes"] > longest_flow["active_minutes"]:
            longest_flow = fb
    top_flow_apps = sorted(flow_app_counts.items(), key=lambda x: x[1], reverse=True)
    afk_count = len(all_afk_gaps)
    avg_afk_len = sum(g["duration_minutes"] for g in all_afk_gaps) / afk_count if afk_count else 0
    longest_afk = max(all_afk_gaps, key=lambda g: g["duration_minutes"]) if all_afk_gaps else None
    day_count = len(days_data)
    device_breakdown = sorted(device_minutes.items(), key=lambda x: x[1], reverse=True)
    return {
        "total_minutes": total_minutes, "day_count": day_count, "top_apps": top_apps,
        "device_breakdown": device_breakdown,
        "peak_windows": peak_windows, "category_totals": dict(category_totals),
        "all_flow_blocks": all_flow_blocks, "longest_flow": longest_flow,
        "top_flow_apps": top_flow_apps, "daily_summaries": daily_summaries,
        "avg_breaks_per_day": afk_count / day_count if day_count else 0,
        "avg_break_length": avg_afk_len, "longest_afk": longest_afk,
    }


def format_weekly_report(week_start, week_end, days_data):
    """Format a weekly summary report."""
    stats = _aggregate_weekly_stats(days_data)
    lines = []
    lines.append(f"## {week_start.isoformat()} → {week_end.isoformat()} WEEKLY SCREENTIME\n")
    total_hrs = fmt_hours(stats["total_minutes"])
    avg_hrs = fmt_hours(stats["total_minutes"] / stats["day_count"]) if stats["day_count"] else "0hrs"
    lines.append(f"**Total:** {total_hrs} across {stats['day_count']} days | Avg {avg_hrs}/day\n")
    if stats["device_breakdown"]:
        lines.append("### Device Breakdown")
        for device, minutes in stats["device_breakdown"]:
            pct = (minutes / stats["total_minutes"] * 100) if stats["total_minutes"] else 0
            lines.append(f"- {device}: {fmt_hours(minutes)} ({pct:.0f}%)")
        lines.append("")
    if stats["peak_windows"]:
        total_dw = sum(w["total_minutes"] for w in stats["peak_windows"])
        lines.append("### Peak Work Hours")
        for i, window in enumerate(stats["peak_windows"][:2]):
            pct = (window["total_minutes"] / total_dw * 100) if total_dw else 0
            label = "Most productive" if i == 0 else "Secondary peak"
            lines.append(f"- {label}: {_fmt_hour(window['start_hour'])}–{_fmt_hour(window['end_hour'])} ({pct:.0f}% of Deep Work)")
        lines.append("")
    lines.append("### Flow Blocks")
    if stats["longest_flow"]:
        lf = stats["longest_flow"]
        start_str = to_local(lf["start"]).strftime("%-I:%M%p").lower()
        day_name = to_local(lf["start"]).strftime("%A")
        lines.append(f"- Longest: {fmt_duration(lf['active_minutes'])} — {lf['app']} ({lf['category']}) — {day_name} {start_str}")
    flow_count = len(stats["all_flow_blocks"])
    avg_flow = flow_count / stats["day_count"] if stats["day_count"] else 0
    lines.append(f"- Total flow blocks: {flow_count} | Avg {avg_flow:.1f}/day")
    if stats["top_flow_apps"]:
        top_fa = ", ".join(f"{app} ({count})" for app, count in stats["top_flow_apps"][:3])
        lines.append(f"- Top flow apps: {top_fa}")
    lines.append("")
    lines.append("### Top Apps")
    for i, (app, minutes) in enumerate(stats["top_apps"][:10], 1):
        lines.append(f"{i}. {app} — {fmt_hours(minutes)}")
    lines.append("")
    lines.append("### AFK Patterns")
    lines.append(f"- Avg breaks/day: {stats['avg_breaks_per_day']:.1f}")
    lines.append(f"- Avg break length: {fmt_duration(stats['avg_break_length'])}")
    if stats["longest_afk"]:
        la = stats["longest_afk"]
        day_name = to_local(la["start"]).strftime("%A")
        lines.append(f"- Longest break: {fmt_duration(la['duration_minutes'])} ({day_name})")
    lines.append("")
    lines.append("### Daily Breakdown")
    lines.append("| Day | Total | Start | End | Flow Blocks | Top App |")
    lines.append("|-----|-------|-------|-----|-------------|---------|")
    for ds in stats["daily_summaries"]:
        day_name = ds["date"].strftime("%a")
        total = fmt_hours(ds["total_minutes"])
        start = ds["start"].strftime("%-I:%M%p").lower() if ds["start"] else "—"
        end = ds["end"].strftime("%-I:%M%p").lower() if ds["end"] else "—"
        lines.append(f"| {day_name} | {total} | {start} | {end} | {ds['flow_count']} | {ds['top_app']} |")
    lines.append("")
    return "\n".join(lines)


def _fmt_hour(hour):
    """Format 24h hour as 12h string (e.g., 23 -> '11pm')."""
    if hour == 0:
        return "12am"
    elif hour == 12:
        return "12pm"
    elif hour < 12:
        return f"{hour}am"
    else:
        return f"{hour - 12}pm"
