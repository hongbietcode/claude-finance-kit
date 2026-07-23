"""Small authenticated HTTP helper for official market-data APIs."""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

from claude_finance_kit._internal.http_client import sanitize_url
from claude_finance_kit.core.exceptions import AuthenticationError, ProviderError, RateLimitError


class MarketHttpClient:
    """JSON HTTP client with provider-specific error classification."""

    def __init__(
        self,
        provider: str,
        allowed_hosts: set[str],
        headers: dict[str, str] | None = None,
        timeout: int = 30,
    ) -> None:
        self.provider = provider.upper()
        self.allowed_hosts = allowed_hosts
        self.headers = headers or {}
        self.timeout = timeout
        self.session = requests.Session()

    def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        safe_url = sanitize_url(url, self.allowed_hosts)
        request_headers = {**self.headers, **(headers or {})}
        try:
            response = self.session.request(
                method.upper(),
                safe_url,
                params=params,
                json=json,
                headers=request_headers,
                timeout=self.timeout,
                allow_redirects=False,
            )
        except requests.RequestException:
            raise ConnectionError(f"{self.provider} request failed") from None

        if response.status_code in {401, 403}:
            raise AuthenticationError(self.provider)
        if 300 <= response.status_code < 400:
            raise ProviderError(
                f"{self.provider} redirect was rejected",
                provider=self.provider,
                error_code=f"{self.provider}_REDIRECT",
            )
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                self.provider,
                int(retry_after) if retry_after and retry_after.isdigit() else None,
            )
        if response.status_code >= 500:
            raise ConnectionError(f"{self.provider} server error HTTP {response.status_code}")
        if response.status_code >= 400:
            raise ProviderError(
                f"{self.provider} rejected request with HTTP {response.status_code}",
                provider=self.provider,
                error_code=f"{self.provider}_HTTP_{response.status_code}",
            )
        try:
            return response.json()
        except ValueError as exc:
            raise ProviderError(
                f"{self.provider} returned invalid JSON",
                provider=self.provider,
                error_code=f"{self.provider}_JSON",
            ) from exc


def records_from_payload(payload: Any) -> list[dict[str, Any]]:
    """Extract records from common official provider response envelopes."""

    if isinstance(payload, list):
        return [record for record in payload if isinstance(record, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("data", "items", "records", "results", "result"):
        value = payload.get(key)
        if isinstance(value, list):
            return [record for record in value if isinstance(record, dict)]
        if isinstance(value, dict):
            for nested_key in ("data", "items", "records", "results"):
                nested = value.get(nested_key)
                if isinstance(nested, list):
                    return [record for record in nested if isinstance(record, dict)]
            return [value]
    return []


def normalize_frame(
    records: list[dict[str, Any]],
    aliases: dict[str, str],
    *,
    numeric: tuple[str, ...] = (),
    required: tuple[str, ...] = (),
    timestamp: str | None = "time",
    deduplicate_timestamp: bool = True,
    source: str,
) -> pd.DataFrame:
    """Normalize provider records with case-insensitive aliases."""

    frame = pd.DataFrame(records)
    if frame.empty:
        return frame
    alias_lookup = {key.lower(): value for key, value in aliases.items()}
    frame = frame.rename(columns={column: alias_lookup.get(str(column).lower(), column) for column in frame.columns})
    missing = [column for column in required if column not in frame]
    if missing:
        raise ProviderError(
            f"{source.upper()} returned an invalid payload missing {missing}",
            provider=source.upper(),
            error_code=f"{source.upper()}_SCHEMA",
        )
    for column in numeric:
        if column in frame:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
            if column in required and frame[column].isna().any():
                raise ProviderError(
                    f"{source.upper()} returned invalid numeric values for '{column}'",
                    provider=source.upper(),
                    error_code=f"{source.upper()}_SCHEMA",
                )
    if timestamp and timestamp in frame:
        numeric_time = pd.to_numeric(frame[timestamp], errors="coerce")
        if numeric_time.notna().all() and not numeric_time.empty:
            magnitude = float(numeric_time.abs().median())
            unit = "ns" if magnitude > 10**17 else "us" if magnitude > 10**14 else "ms" if magnitude > 10**11 else "s"
            frame[timestamp] = pd.to_datetime(
                numeric_time,
                unit=unit,
                utc=True,
                errors="coerce",
            )
        else:
            frame[timestamp] = pd.to_datetime(frame[timestamp], utc=True, errors="coerce")
        if timestamp in required and frame[timestamp].isna().any():
            raise ProviderError(
                f"{source.upper()} returned invalid timestamps",
                provider=source.upper(),
                error_code=f"{source.upper()}_SCHEMA",
            )
        frame = frame.sort_values(timestamp)
        if deduplicate_timestamp:
            frame = frame.drop_duplicates(subset=[timestamp], keep="last")
    frame = frame.reset_index(drop=True)
    frame.attrs["source"] = source.upper()
    return frame
