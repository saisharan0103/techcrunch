from datetime import date, time

from src.scheduler import build_schedule


def test_build_schedule_even_spacing():
    schedule = build_schedule(
        count=4,
        run_date=date(2025, 9, 16),
        tz_name="Asia/Kolkata",
        start_time=time(2, 0),
        end_time=time(10, 0),
    )
    assert len(schedule) == 4
    assert schedule[0].scheduled_at.hour == 2
    assert schedule[-1].scheduled_at.hour <= 9


def test_build_schedule_empty_when_zero_count():
    schedule = build_schedule(
        count=0,
        run_date=date(2025, 9, 16),
        tz_name="Asia/Kolkata",
        start_time=time(2, 0),
        end_time=time(10, 0),
    )
    assert schedule == []
