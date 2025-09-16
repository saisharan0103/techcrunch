"""Scheduling helpers for spacing tweets across a day."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


@dataclass
class ScheduleSlot:
    scheduled_at: datetime
    item_index: int


def build_schedule(
    count: int,
    run_date: date,
    tz_name: str,
    start_time: time,
    end_time: time | None = None,
) -> list[ScheduleSlot]:
    """Distribute count items evenly between start_time and end_time within the given timezone."""
    if count <= 0:
        return []

    tz = ZoneInfo(tz_name)
    run_start = datetime.combine(run_date, start_time, tz)

    if end_time is None:
        end_time = time(23, 59)
    run_end = datetime.combine(run_date, end_time, tz)

    if run_end <= run_start:
        raise ValueError("end_time must be after start_time")

    total_seconds = (run_end - run_start).total_seconds()
    interval_seconds = total_seconds / max(count, 1)

    schedule: list[ScheduleSlot] = []
    for idx in range(count):
        offset_seconds = interval_seconds * idx
        scheduled_at = run_start + timedelta(seconds=offset_seconds)
        schedule.append(ScheduleSlot(scheduled_at=scheduled_at, item_index=idx))
    return schedule
