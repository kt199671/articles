"""Configuration constants for weekly news automation."""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
MAGAZINE_NAME = "週刊コワーキングスペース"
MAGAZINE_PATH = PROJECT_ROOT / "note" / "magazine" / MAGAZINE_NAME

# Article specifications
TARGET_CHAR_COUNT_MIN = 1500
TARGET_CHAR_COUNT_MAX = 2500
NEWS_ITEMS_MIN = 3
NEWS_ITEMS_MAX = 5
ITEM_CHAR_COUNT_MIN = 200
ITEM_CHAR_COUNT_MAX = 400

# Week number format (ISO week)
WEEK_FORMAT = "%Y年%V週"  # e.g., "2026年01週"

# API timeouts (seconds)
TAVILY_TIMEOUT = 30
NOTE_API_TIMEOUT = 30
GEMINI_TIMEOUT = 60

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "[%(asctime)s] %(levelname)s: %(message)s"

# Search queries for Tavily
SEARCH_QUERIES = [
    "コワーキングスペース トレンド 最新ニュース",
    "coworking space trends news 2026",
    "リモートワーク シェアオフィス 新規開業",
    "coworking space technology innovation",
]

# note.com API endpoints
NOTE_BASE_URL = "https://note.com"
NOTE_LOGIN_ENDPOINT = f"{NOTE_BASE_URL}/api/v1/login"
NOTE_NOTES_ENDPOINT = f"{NOTE_BASE_URL}/api/v2/notes"
NOTE_DASHBOARD_URL = f"{NOTE_BASE_URL}/dashboard"
