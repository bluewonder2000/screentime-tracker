"""Categorize apps and window titles into activity categories."""

from config import APP_CATEGORIES, YOUTUBE_ENTERTAINMENT_KEYWORDS


def categorize(app_name, title=""):
    """Categorize an app + window title into an activity category.

    Args:
        app_name: Application name (e.g. "Google Chrome", "Code")
        title: Window title (e.g. "How to build X - YouTube")

    Returns:
        Category string (e.g. "Deep Work", "Entertainment", "Learning")
    """
    app_lower = app_name.lower()
    title_lower = title.lower()

    # YouTube special handling: check window title for YouTube
    if "youtube" in title_lower:
        return _categorize_youtube(title_lower)

    # Match against app category mappings
    for pattern, category in APP_CATEGORIES.items():
        if pattern in app_lower:
            return category

    return "Other"


def _categorize_youtube(title_lower):
    """Categorize YouTube content by video title keywords."""
    for keyword in YOUTUBE_ENTERTAINMENT_KEYWORDS:
        if keyword in title_lower:
            return "Entertainment"
    return "Learning"
