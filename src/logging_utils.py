"""Utility helpers for structured logging and run artifacts."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

from .typefully import TypefullyDraft


def write_daily_log(log_dir: Path, run_date: datetime, drafts: Iterable[TypefullyDraft]) -> Path:
    """Write a markdown log summarizing scheduled tweets for the run."""
    log_dir.mkdir(parents=True, exist_ok=True)
    file_path = log_dir / f"{run_date:%Y-%m-%d}.md"

    lines = [
        f"# Tweets scheduled for {run_date:%Y-%m-%d}",
        "",
    ]
    for index, draft in enumerate(drafts, 1):
        lines.append(f"## Tweet {index}")
        lines.append("")
        lines.append(f"- Scheduled: {draft.schedule_date.isoformat()}")
        lines.append("- Content:")
        lines.append("")
        lines.append("```text")
        lines.append(draft.content)
        lines.append("```")
        lines.append("")

    file_path.write_text("\n".join(lines), encoding="utf-8")
    return file_path
