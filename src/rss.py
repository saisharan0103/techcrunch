"""TechCrunch RSS ingestion."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Iterable, List

import feedparser
import requests
from dateutil import parser as date_parser

from .utils import retry

logger = logging.getLogger(__name__)


@dataclass
class FeedItem:
    title: str
    link: str
    published: datetime
    summary: str


def fetch_feed(url: str, attempts: int = 3) -> Iterable[FeedItem]:
    """Fetch RSS items from the given URL with retries."""

    def _get() -> str:
        logger.debug("Fetching RSS feed: %s", url)
        response = requests.get(url, headers={"User-Agent": "techcrunch-gemini-bot/1.0"}, timeout=30)
        response.raise_for_status()
        return response.text

    feed_text = retry(_get, attempts=attempts)
    parsed = feedparser.parse(feed_text)

    if getattr(parsed, "bozo", False):
        logger.warning("Feed parse flagged bozo=True: %s", getattr(parsed, "bozo_exception", ""))

    items: List[FeedItem] = []
    for entry in parsed.entries:
        published = _parse_datetime(entry.get("published"))
        items.append(
            FeedItem(
                title=(entry.get("title") or "").strip(),
                link=(entry.get("link") or "").strip(),
                published=published,
                summary=(entry.get("summary") or entry.get("description") or "").strip(),
            )
        )
    logger.debug("Parsed %d items from feed", len(items))
    return items


def filter_items_for_date(items: Iterable[FeedItem], target_date: date, tz_name: str) -> list[FeedItem]:
    from zoneinfo import ZoneInfo

    tz = ZoneInfo(tz_name)
    filtered: list[FeedItem] = []
    for item in items:
        item_local_date = item.published.astimezone(tz).date()
        if item_local_date == target_date:
            filtered.append(item)
    logger.debug("Filtered %d items for %s", len(filtered), target_date)
    return filtered


def _parse_datetime(value: str | None) -> datetime:
    if not value:
        return datetime.now(tz=timezone.utc)
    dt = date_parser.parse(value)
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
