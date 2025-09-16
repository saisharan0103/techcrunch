"""Configuration management utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass
class Settings:
    techcrunch_feed_url: str
    gemini_api_key: str
    typefully_api_key: str
    timezone: str = "Asia/Kolkata"
    gemini_model: str = "gemini-pro"
    max_attempts: int = 3
    dry_run: bool = False
    logs_dir: Path = field(default_factory=lambda: Path("logs"))
    max_feed_pages: int = 10


def load_settings(env_file: Optional[Path] = None) -> Settings:
    """Load configuration from environment variables or an .env file."""
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()

    return Settings(
        techcrunch_feed_url=_require_env("TECHCRUNCH_FEED_URL"),
        gemini_api_key=_require_env("GEMINI_API_KEY"),
        typefully_api_key=_require_env("TYPEFULLY_API_KEY"),
        timezone=_get_env("TIMEZONE", default="Asia/Kolkata"),
        gemini_model=_get_env("GEMINI_MODEL", default="gemini-1.5-pro"),
        max_attempts=_get_int("MAX_RETRIES", default=3),
        dry_run=_get_bool("DRY_RUN", default=False),
        logs_dir=Path(_get_env("LOGS_DIR", default="logs")),
        max_feed_pages=_get_int("FEED_MAX_PAGES", default=10),
    )


def _require_env(name: str) -> str:
    value = _get_env(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    import os

    return os.getenv(name, default)


def _get_int(name: str, default: int) -> int:
    raw = _get_env(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError as exc:  # noqa: F841
        raise ValueError(f"Environment variable {name} must be an integer")


def _get_bool(name: str, default: bool) -> bool:
    raw = _get_env(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}
