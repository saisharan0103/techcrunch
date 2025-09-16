"""Typefully API client for scheduling tweets."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Sequence

import requests

from .utils import retry

logger = logging.getLogger(__name__)


@dataclass
class TypefullyDraft:
    content: str
    schedule_date: datetime


class TypefullyClient:
    def __init__(self, api_key: str, max_attempts: int = 3) -> None:
        self.api_key = api_key
        self.max_attempts = max_attempts
        self.base_url = "https://api.typefully.com/v1"
        self.session = requests.Session()

    def schedule(self, drafts: Sequence[TypefullyDraft]) -> list[str]:
        if not drafts:
            return []
        ids: list[str] = []
        for draft in drafts:
            ids.append(self._schedule_single(draft))
        return ids

    def _schedule_single(self, draft: TypefullyDraft) -> str:
        url = f"{self.base_url}/drafts/"
        headers = {
            "X-API-KEY": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "content": draft.content,
            "schedule-date": draft.schedule_date.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "threadify": False,
            "share": True,
        }

        def _call() -> str:
            logger.debug("Scheduling tweet at %s", payload["schedule-date"])
            response = self.session.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            draft_id = data.get("id") or data.get("draft", {}).get("id")
            if not draft_id:
                raise ValueError("Typefully response missing draft id")
            return str(draft_id)

        return retry(_call, attempts=self.max_attempts)
