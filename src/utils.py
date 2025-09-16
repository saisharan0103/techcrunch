"""Shared utility helpers."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def retry(operation: Callable[[], T], attempts: int = 3, backoff_seconds: float = 2.0) -> T:
    """Retry an operation up to ``attempts`` times with exponential backoff."""
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except Exception as exc:  # noqa: BLE001 - propagate final failure
            last_error = exc
            if attempt == attempts:
                break
            sleep_for = backoff_seconds ** (attempt - 1)
            time.sleep(sleep_for)
    if last_error is None:
        raise RuntimeError("retry operation failed without raising an exception")
    raise last_error
