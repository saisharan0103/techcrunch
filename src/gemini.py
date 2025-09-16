"""Gemini API integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable

import requests

from .utils import retry

logger = logging.getLogger(__name__)


@dataclass
class GeminiPrompt:
    title: str
    summary: str
    link: str


@dataclass
class GeminiResponse:
    content: str


class GeminiClient:
    def __init__(self, api_key: str, model: str = "gemini-pro", max_attempts: int = 3) -> None:
        self.api_key = api_key
        self.model = model
        self.max_attempts = max_attempts
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.session = requests.Session()

    def generate(self, prompt: GeminiPrompt) -> GeminiResponse:
        """Generate tweet content from Gemini with retries."""
        endpoint = f"{self.base_url}/{self.model}:generateContent"
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": self._build_prompt(prompt),
                        }
                    ]
                }
            ]
        }
        params = {"key": self.api_key}

        def _call() -> GeminiResponse:
            logger.debug("Calling Gemini for title: %s", prompt.title)
            response = self.session.post(endpoint, params=params, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            text = self._parse_response(data)
            return GeminiResponse(content=text)

        return retry(_call, attempts=self.max_attempts)

    def _build_prompt(self, prompt: GeminiPrompt) -> str:
        return (
            "You are a social media assistant for a tech newsletter. "
            "Write a concise, engaging tweet summarizing the TechCrunch story below. "
            "Do not include hashtags, URLs, or media references. Keep it under 250 characters.\n\n"
            f"Title: {prompt.title}\n"
            f"Summary: {prompt.summary}\n"
        )

    def _parse_response(self, data: dict) -> str:
        candidates = data.get("candidates", [])
        for candidate in candidates:
            content = candidate.get("content", {})
            parts = content.get("parts", [])
            for part in parts:
                text = part.get("text")
                if text:
                    cleaned = text.strip()
                    if cleaned:
                        return cleaned
        raise ValueError("Gemini response did not contain text")


def generate_batch(client: GeminiClient, prompts: Iterable[GeminiPrompt]) -> list[GeminiResponse]:
    responses: list[GeminiResponse] = []
    for prompt in prompts:
        responses.append(client.generate(prompt))
    return responses
