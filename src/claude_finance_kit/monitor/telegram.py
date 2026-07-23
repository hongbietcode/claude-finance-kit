"""Outbound-only Telegram Bot API notifier."""

from __future__ import annotations

import asyncio
import os
from collections.abc import Callable
from typing import Any

import requests

from claude_finance_kit.core.exceptions import AuthenticationError, RateLimitError


class TelegramNotifier:
    """Chunk, throttle, and retry Telegram messages without logging secrets."""

    MAX_LENGTH = 4096

    def __init__(
        self,
        token: str | None = None,
        chat_id: str | None = None,
        *,
        timeout: int = 20,
        max_retries: int = 3,
        transport: Callable[..., Any] | None = None,
    ) -> None:
        self.token = token or os.getenv("CFK_TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("CFK_TELEGRAM_CHAT_ID")
        if not self.token or not self.chat_id:
            raise AuthenticationError(
                "TELEGRAM",
                "CFK_TELEGRAM_BOT_TOKEN and CFK_TELEGRAM_CHAT_ID are required",
            )
        self.timeout = timeout
        self.max_retries = max_retries
        self.transport = transport or requests.post

    @classmethod
    def chunks(cls, text: str) -> list[str]:
        chunks: list[str] = []
        remaining = text
        while remaining:
            if len(remaining) <= cls.MAX_LENGTH:
                chunks.append(remaining)
                break
            boundary = remaining.rfind("\n", 0, cls.MAX_LENGTH)
            if boundary < cls.MAX_LENGTH // 2:
                boundary = cls.MAX_LENGTH
            chunks.append(remaining[:boundary])
            remaining = remaining[boundary:].lstrip("\n")
        return chunks

    async def send(self, text: str) -> None:
        for chunk in self.chunks(text):
            await self._send_chunk(chunk)

    async def check(self) -> None:
        """Validate the bot token without sending a message."""

        endpoint = f"https://api.telegram.org/bot{self.token}/getMe"
        try:
            response = await asyncio.to_thread(
                self.transport,
                endpoint,
                timeout=self.timeout,
            )
        except Exception:
            raise ConnectionError("Telegram getMe transport failed") from None
        if response.status_code == 200:
            return
        if response.status_code in {401, 403}:
            raise AuthenticationError("TELEGRAM")
        if response.status_code == 429:
            raise RateLimitError("TELEGRAM")
        raise ConnectionError(f"Telegram getMe failed with HTTP {response.status_code}")

    async def _send_chunk(self, text: str) -> None:
        endpoint = f"https://api.telegram.org/bot{self.token}/sendMessage"
        for attempt in range(self.max_retries):
            try:
                response = await asyncio.to_thread(
                    self.transport,
                    endpoint,
                    json={
                        "chat_id": self.chat_id,
                        "text": text,
                        "disable_web_page_preview": True,
                    },
                    timeout=self.timeout,
                )
            except Exception:
                raise ConnectionError("Telegram sendMessage transport failed") from None
            if response.status_code == 200:
                return
            if response.status_code in {401, 403}:
                raise AuthenticationError("TELEGRAM")
            if response.status_code == 429:
                try:
                    retry_after = int(response.json().get("parameters", {}).get("retry_after", 1))
                except (TypeError, ValueError):
                    retry_after = 1
                if attempt + 1 == self.max_retries:
                    raise RateLimitError("TELEGRAM", retry_after)
                await asyncio.sleep(min(retry_after, 60))
                continue
            if response.status_code >= 500 and attempt + 1 < self.max_retries:
                await asyncio.sleep(2**attempt)
                continue
            raise ConnectionError(f"Telegram sendMessage failed with HTTP {response.status_code}")
