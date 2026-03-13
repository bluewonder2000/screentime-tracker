"""Configuration for screen time tracker."""

from pathlib import Path

# ActivityWatch API — one entry per device
DEVICES = [
    {"name": "Mac", "url": "http://localhost:5600/api/0"},
    # {"name": "Windows", "url": "http://<tailscale-ip>:5600/api/0"},
]

# Obsidian output
OUTPUT_DIR = Path.home() / "Documents/main/CALENDAR/Weekly Screentime"

# Weekly report config
WEEK_START_HOUR = 12  # Sunday noon boundary for weekly reports

# App → Category mappings
# Keys are lowercased app names (or substrings)
# Apps to completely exclude from tracking (lock screen, system UI, etc.)
EXCLUDED_APPS = [
    "loginwindow",
    "screensaver",
    "universalcontrol",
]

APP_CATEGORIES = {
    # Deep Work
    "code": "Deep Work",
    "xcode": "Deep Work",
    "cursor": "Deep Work",
    "warp": "Deep Work",
    "capcut": "Deep Work",
    "figma": "Deep Work",
    "terminal": "Deep Work",
    "iterm": "Deep Work",
    "obsidian": "Deep Work",
    "notion": "Deep Work",

    # Communication
    "slack": "Communication",
    "discord": "Communication",
    "messages": "Communication",
    "mail": "Communication",
    "zoom": "Communication",
    "facetime": "Communication",
    "telegram": "Communication",
    "whatsapp": "Communication",

    # Productivity / Utilities
    "todoist": "Productivity",
    "chatgpt": "Productivity",
    "preview": "Productivity",
    "finder": "Productivity",
    "photos": "Productivity",
    "find my": "Productivity",
    "calendar": "Productivity",
    "notion calendar": "Productivity",
    "notes": "Productivity",
    "reminders": "Productivity",
    "system settings": "Productivity",
    "cold turkey": "Productivity",
    "nomachine": "Deep Work",

    # Entertainment (non-YouTube)
    "netflix": "Entertainment",
    "spotify": "Entertainment",
    "twitch": "Entertainment",

    # Browsing (fallback for Chrome/Safari/Firefox without specific URL match)
    "chrome": "Browsing",
    "safari": "Browsing",
    "firefox": "Browsing",
    "arc": "Browsing",
}

# YouTube entertainment keywords (case-insensitive)
# If a YouTube video title contains any of these → Entertainment
# Otherwise → Learning
YOUTUBE_ENTERTAINMENT_KEYWORDS = [
    "valorant", "nba", "basketball", "gaming", "highlights",
    "funny", "memes", "netflix", "twitch",
    "f1", "formula 1", "formula1", "grand prix",
    "anime", "naruto", "one piece", "jujutsu", "dragon ball", "crunchyroll",
    "fortnite", "league of legends", "minecraft", "gta",
    "reaction", "prank", "tiktok",
]

# Timeline detection thresholds
FLOW_BLOCK_MIN_MINUTES = 30       # Minimum minutes for a "flow block"
MERGE_GAP_SECONDS = 60            # Merge consecutive same-app events within this gap
TIMELINE_MIN_SECONDS = 30         # Hide blocks shorter than this from timeline table
AFK_MIN_MINUTES = 5               # Minimum AFK gap to report
DAY_START_HOUR = 0                # A "day" runs from 12am to 12am (standard midnight boundary)

# Category display order
CATEGORY_ORDER = ["Deep Work", "Productivity", "Communication", "Learning", "Entertainment", "Browsing", "Other"]
