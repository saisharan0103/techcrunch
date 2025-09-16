"""TechCrunch RSS ingestion."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Iterable, List
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

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


def build_paged_url(base_url: str, page: int) -> str:
    if page <= 1:
        return base_url
    parsed = urlparse(base_url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["paged"] = str(page)
    new_query = urlencode(query, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


def fetch_feed(url: str, attempts: int = 3, pages: int = 1) -> Iterable[FeedItem]:
    """Fetch RSS items from the given URL (optionally across multiple paged feeds)."""

    def _get(target_url: str) -> str:
        logger.debug("Fetching RSS feed: %s", target_url)
        response = requests.get(target_url, headers={"User-Agent": "techcrunch-gemini-bot/1.0"}, timeout=30)
        response.raise_for_status()
        return response.text

    items: List[FeedItem] = []
    seen_links: set[str] = set()

    for page in range(1, pages + 1):
        target_url = build_paged_url(url, page)
        try:
            feed_text = retry(lambda: _get(target_url), attempts=attempts)
        except Exception:  # noqa: BLE001
            logger.exception("Failed to fetch RSS page %s", target_url)
            continue

        parsed = feedparser.parse(feed_text)

        if getattr(parsed, "bozo", False):
            logger.warning("Feed parse flagged bozo=True for %s: %s", target_url, getattr(parsed, "bozo_exception", ""))

        page_items = 0
        for entry in parsed.entries:
            published = _parse_datetime(entry.get("published") or entry.get("pubDate"))
            link = (entry.get("link") or "").strip()
            if link and link in seen_links:
                continue
            seen_links.add(link)
            items.append(
                FeedItem(
                    title=(entry.get("title") or "").strip(),
                    link=link,
                    published=published,
                    summary=(entry.get("summary") or entry.get("description") or "").strip(),
                )
            )
            page_items += 1

        logger.debug("Parsed %d items from feed page %s", page_items, target_url)

        if page_items == 0:
            logger.info("No items returned from %s; stopping pagination", target_url)
            break

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
