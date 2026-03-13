# Multi-Device Support + Weekly Reports

## Overview

Extend the screentime tracker to support multiple devices (Mac + Windows via Tailscale) and generate weekly summary reports focused on behavioral patterns.

## Multi-Device Support

### Config

`config.py` adds a `DEVICES` list:

```python
DEVICES = [
    {"name": "Mac", "url": "http://localhost:5600/api/0"},
    {"name": "Windows", "url": "http://<tailscale-ip>:5600/api/0"},
]
```

Replaces the current single `AW_BASE_URL`.

### Fetching

- `fetcher.py` iterates over all devices, discovering buckets and fetching events per device.
- Events are tagged with their device name.
- If a device is unreachable, log a warning and continue with available devices.

### Daily Report Changes

- Timeline table gets a **Device** column.
- Category totals and flow blocks aggregate across all devices.
- AFK gaps are tracked per-device (AFK on Mac doesn't mean AFK on Windows).
- Filename unchanged: `2026-03-11 SCREENTIME.md`.
- If all devices are offline or have no data for a day, skip that day.

## Weekly Report

### Trigger

`run.py --weekly` generates the weekly report.

### Week Boundary

Sunday 12:00pm to Sunday 12:00pm. Sunday's data is split between two weeks at the noon boundary.

### Data Source

Calls `build_timeline()` for each of the 7 days in the week (re-fetches from AW API via the same daily pipeline). No JSON caching — if a day's data isn't available, that day is skipped.

### Output

File: `2026-03-08 WEEKLY.md` (named by the Sunday the week starts).
Location: same folder as daily reports (`~/Documents/main/CALENDAR/Weekly Screentime/`).

### Report Structure

```
## 2026-03-08 → 2026-03-14 WEEKLY SCREENTIME

**Total:** 38.2hrs across 7 days | Avg 5.5hrs/day

### Peak Work Hours
- Most productive: 11pm–2am (35% of Deep Work)
- Secondary peak: 2pm–5pm (22% of Deep Work)

### Flow Blocks
- Longest: 2h 15m — Cursor (Deep Work) — Tuesday 11:30pm
- Total flow blocks: 18 | Avg 2.6/day
- Top flow apps: Cursor (9), Obsidian (4), Figma (3)

### Top Apps
1. Cursor — 12.3hrs
2. Chrome — 8.1hrs
3. Discord — 3.2hrs
4. Obsidian — 2.8hrs
5. Spotify — 2.1hrs

### AFK Patterns
- Avg breaks/day: 4.2
- Avg break length: 22m
- Longest break: 1h 45m (Wednesday)

### Daily Breakdown
| Day | Total | Start | End | Flow Blocks | Top App |
|-----|-------|-------|-----|-------------|---------|
| Sun | 4.2hrs | 12:30pm | 1:15am | 2 | Cursor |
| Mon | 6.1hrs | 10:15am | 2:30am | 3 | Chrome |
| ... |
```

### Sections

1. **Summary line** — total hours, day count, daily average.
2. **Peak Work Hours** — time-of-day breakdown of when Deep Work category is concentrated. Shows primary and secondary peak windows.
3. **Flow Blocks** — longest session of the week, total count with daily average, top apps by flow block count.
4. **Top Apps** — top 5-10 apps ranked by total time across the week.
5. **AFK Patterns** — average breaks per day, average break length, longest break with day label.
6. **Daily Breakdown** — table with per-day totals, first/last activity times, flow block count, and top app.

## New Files

- `weekly_formatter.py` — aggregation logic and markdown formatting for weekly reports.

## Modified Files

- `config.py` — `DEVICES` list replaces `AW_BASE_URL`, add `WEEK_START_HOUR = 12` config.
- `fetcher.py` — multi-device iteration, device tagging on events, graceful failure per device.
- `formatter.py` — add Device column to timeline table.
- `run.py` — add `--weekly` flag, week boundary logic (Sunday noon to Sunday noon).

## Git / GitHub

Initialize git repo, push to GitHub so both Mac and Windows can clone and run the script.
