"""Configuration for Coworking Research Lab automation."""

from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
MAGAZINE_NAME = "コワーキングの場づくり研究室"
MAGAZINE_PATH = PROJECT_ROOT / "note" / "magazine" / MAGAZINE_NAME

# Search configuration
SEARCH_QUERIES = [
    "コワーキングスペース 研究 論文 最新",
    "coworking space research study 2026",
    "サードプレイス 働き方 トレンド",
    "ウェルビーイング オフィス 研究",
    "フレキシブルオフィス 効果 調査",
    "workplace wellbeing productivity research",
    "hybrid work environment study",
]

# Article parameters (longer for research articles)
TARGET_CHAR_COUNT_MIN = 5000
TARGET_CHAR_COUNT_MAX = 8000
SECTIONS_MIN = 5
SECTIONS_MAX = 8

# API timeouts (ms)
GEMINI_TIMEOUT = 120000  # 2 minutes for longer content
TAVILY_TIMEOUT = 60000   # 1 minute

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

# Week format
WEEK_FORMAT = "%Y年%V週"
