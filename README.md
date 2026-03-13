# Screen Time Tracker

Pulls ActivityWatch data and generates daily screen time reports as Obsidian markdown notes.

## Setup

1. Install and run [ActivityWatch](https://activitywatch.net/) on your Mac
2. Ensure the API is accessible at `http://localhost:5600`

No external dependencies — uses Python stdlib only.

## Usage

```bash
# Yesterday's report (default)
python3 run.py

# Today so far
python3 run.py --today

# Specific date
python3 run.py --date 2026-03-12

# Past 7 days
python3 run.py --week
```

Reports are written to `~/Documents/main/CALENDAR/Weekly Screentime/YYYY-MM-DD.md`.

## Configuration

Edit `config.py` to:
- Add/change app → category mappings (`APP_CATEGORIES`)
- Add YouTube entertainment keywords (`YOUTUBE_ENTERTAINMENT_KEYWORDS`)
- Exclude apps from tracking (`EXCLUDED_APPS`)
- Adjust flow block detection thresholds
