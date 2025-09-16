from datetime import datetime, timezone
from pathlib import Path

from src.logging_utils import write_daily_log
from src.typefully import TypefullyDraft


def test_write_daily_log(tmp_path: Path):
    drafts = [
        TypefullyDraft(content="Example tweet", schedule_date=datetime(2025, 9, 16, 10, 0, tzinfo=timezone.utc)),
    ]
    log_path = write_daily_log(tmp_path, datetime(2025, 9, 16, 1, 0, tzinfo=timezone.utc), drafts)
    assert log_path.exists()
    text = log_path.read_text()
    assert "Example tweet" in text
