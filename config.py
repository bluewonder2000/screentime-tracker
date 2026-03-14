"""Configuration for screen time tracker."""

from pathlib import Path

# iPhone Biome config
IPHONE_BIOME_UUID = "DB143242-2D71-45B3-B6B0-7A2CF1F7F75A"
IPHONE_BIOME_PATH = Path.home() / "Library/Biome/streams/restricted/App.InFocus/remote" / IPHONE_BIOME_UUID
IPHONE_SESSION_CAP_SECONDS = 600  # 10 min max per event

BUNDLE_ID_MAP = {
    "com.burbn.instagram": "Instagram",
    "com.apple.MobileSMS": "iMessage",
    "com.zhiliaoapp.musically": "TikTok",
    "com.apple.mobilesafari": "Safari",
    "com.spotify.client": "Spotify",
    "com.openai.chat": "ChatGPT",
    "com.toyopagroup.picaboo": "Snapchat",
    "com.atebits.Tweetie2": "X",
    "com.google.Gmail": "Gmail",
    "com.todoist.ios": "Todoist",
    "com.apple.mobileslideshow": "Photos",
    "com.apple.camera": "Camera",
    "com.apple.Preferences": "Settings",
    "com.apple.findmy": "Find My",
    "com.apple.mobilephone": "Phone",
    "com.apple.AppStore": "App Store",
    "com.swoosh.mobile": "Nike",
    "com.transact.mobileorder": "Transact",
    "com.marius-genton.bruindining": "BruinDining",
    "com.google.Drive": "Google Drive",
    "net.whatsapp.WhatsApp": "WhatsApp",
    "com.apple.BodyScan": "Bodyscan",
}

# iPhone apps to exclude (system UI, overlays)
IPHONE_EXCLUDED_APPS = [
    "com.apple.SpringBoard",
    "com.apple.SleepLockScreen",
    "com.apple.EyeReliefUI",
    "com.apple.control-center",
    "com.apple.HeadphoneProxService",
    "com.apple.AuthKitUIService",
    "com.apple.LocalAuthenticationUIService",
    "com.apple.PassbookUIService",
    "com.apple.InCallService",
    "com.apple.ClockAngel",
    "com.apple.springboard.app-library",
    "com.apple.springboard.today-view",
]

# ActivityWatch API — one entry per device
DEVICES = [
    {"name": "Mac", "url": "http://localhost:5600/api/0"},
    {"name": "Windows", "url": "http://100.123.56.28:5600/api/0"},
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
    "imessage": "Communication",
    "snapchat": "Communication",
    "x": "Communication",
    "phone": "Communication",

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

    "bodyscan": "Productivity",
    "transact": "Productivity",
    "bruindining": "Productivity",
    "google drive": "Productivity",
    "fitai": "Productivity",

    # Entertainment (non-YouTube)
    "netflix": "Entertainment",
    "spotify": "Entertainment",
    "twitch": "Entertainment",
    "instagram": "Entertainment",
    "tiktok": "Entertainment",
    "nike": "Entertainment",

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
MERGE_ABSORB_SECONDS = 120        # Absorb brief app switches shorter than this back into surrounding app
TIMELINE_MIN_SECONDS = 30         # Hide blocks shorter than this from timeline table
AFK_MIN_MINUTES = 5               # Minimum AFK gap to report
DAY_START_HOUR = 0                # A "day" runs from 12am to 12am (standard midnight boundary)

# Category display order
CATEGORY_ORDER = ["Deep Work", "Productivity", "Communication", "Learning", "Entertainment", "Browsing", "Other"]
