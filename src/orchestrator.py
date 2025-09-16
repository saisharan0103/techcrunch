"""Main orchestration flow."""

from __future__ import annotations

import logging
from datetime import datetime, time, timedelta
from typing import Iterable

from zoneinfo import ZoneInfo

from .config import Settings, load_settings
from .gemini import GeminiClient, GeminiPrompt
from .logging_utils import write_daily_log
from .rss import FeedItem, fetch_feed, filter_items_for_date
from .scheduler import build_schedule
from .typefully import TypefullyClient, TypefullyDraft

logger = logging.getLogger(__name__)

SCHEDULE_START_TIME = time(2, 0)
SCHEDULE_END_TIME = time(23, 0)


def run(settings: Settings | None = None) -> None:
    settings = settings or load_settings()
    tz = ZoneInfo(settings.timezone)

    run_now = datetime.now(tz)
    target_date = (run_now - timedelta(days=1)).date()
    logger.info("Starting TechCrunch automation for %s", target_date.isoformat())

    items = list(
        fetch_feed(
            settings.techcrunch_feed_url,
            attempts=settings.max_attempts,
            pages=settings.max_feed_pages,
        )
    )
    filtered_items = sorted(
        filter_items_for_date(items, target_date=target_date, tz_name=settings.timezone),
        key=lambda item: item.published,
    )

    if not filtered_items:
        logger.info("No TechCrunch items found for %s", target_date.isoformat())
        return

    schedule_slots = build_schedule(
        count=len(filtered_items),
        run_date=run_now.date(),
        tz_name=settings.timezone,
        start_time=SCHEDULE_START_TIME,
        end_time=SCHEDULE_END_TIME,
    )

    if schedule_slots:
        logger.info(
            "Scheduling %d tweets between %s and %s (%s)",
            len(schedule_slots),
            schedule_slots[0].scheduled_at.isoformat(),
            schedule_slots[-1].scheduled_at.isoformat(),
            settings.timezone,
        )

    gemini_client = GeminiClient(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        max_attempts=settings.max_attempts,
    )
    prompts = _build_prompts(filtered_items)

    responses = []
    for prompt in prompts:
        response = gemini_client.generate(prompt)
        responses.append(response)

    drafts = [
        TypefullyDraft(content=response.content, schedule_date=schedule_slots[idx].scheduled_at)
        for idx, response in enumerate(responses)
    ]

    if settings.dry_run:
        logger.info("Dry run enabled; skipping publishing to Typefully")
    else:
        typefully_client = TypefullyClient(api_key=settings.typefully_api_key, max_attempts=settings.max_attempts)
        draft_ids = typefully_client.schedule(drafts)
        logger.info("Scheduled %d drafts via Typefully", len(draft_ids))

    log_path = write_daily_log(settings.logs_dir, run_now, drafts)
    logger.info("Wrote daily log to %s", log_path)


def _build_prompts(items: Iterable[FeedItem]) -> list[GeminiPrompt]:
    prompts: list[GeminiPrompt] = []
    for item in items:
        summary = item.summary.strip()
        if len(summary) > 500:
            summary = summary[:497] + "..."
        prompts.append(
            GeminiPrompt(
                title=item.title.strip(),
                summary=summary,
                link=item.link,
            )
        )
    return prompts


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    run()
