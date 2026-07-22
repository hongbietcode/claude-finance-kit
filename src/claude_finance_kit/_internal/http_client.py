"""Shared HTTP client with retry and timeout support."""

import json
import logging
from collections.abc import Iterable
from typing import Any, Optional, Union
from urllib.parse import urlsplit, urlunsplit

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_WAIT_MIN = 1
DEFAULT_RETRY_WAIT_MAX = 8



def sanitize_url(url: str, allowed_hosts: Iterable[str] | None = None) -> str:
    """Validate and normalize an HTTPS provider URL before requesting it."""
    if not isinstance(url, str) or any(ord(char) < 32 for char in url):
        raise ValueError("Provider URL must be a valid string without control characters.")

    parsed = urlsplit(url.strip())
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        raise ValueError("Provider URL must use HTTPS and include a hostname.")
    if parsed.username or parsed.password or parsed.fragment:
        raise ValueError("Provider URL cannot include credentials or a fragment.")

    if allowed_hosts is not None:
        hosts = {host.lower() for host in allowed_hosts}
        if parsed.hostname.lower() not in hosts:
            raise ValueError(f"Provider host '{parsed.hostname}' is not allowed.")

    hostname = parsed.hostname.lower()
    netloc = f"{hostname}:{parsed.port}" if parsed.port else hostname
    path = parsed.path or "/"
    return urlunsplit(("https", netloc, path, parsed.query, ""))


def _do_request(
    url: str,
    headers: dict[str, str],
    method: str,
    params: Optional[dict],
    payload: Optional[Union[dict, str]],
    timeout: int,
) -> Any:
    """Execute a single HTTP request and return parsed JSON."""
    try:
        kwargs: dict[str, Any] = {
            "headers": headers,
            "timeout": timeout,
        }
        if method.upper() == "GET":
            kwargs["params"] = params
            response = requests.get(url, **kwargs)
        else:
            if isinstance(payload, dict):
                kwargs["data"] = json.dumps(payload)
            elif isinstance(payload, str):
                kwargs["data"] = payload
            response = requests.post(url, **kwargs)

        if response.status_code != 200:
            raise ConnectionError(
                f"HTTP {response.status_code} {response.reason} from {url}"
            )
        try:
            return response.json()
        except (requests.exceptions.JSONDecodeError, ValueError) as exc:
            raise ConnectionError(f"Invalid JSON response from {url}") from exc

    except requests.exceptions.RequestException as exc:
        raise ConnectionError(f"Request failed: {exc}") from exc


@retry(
    retry=retry_if_exception_type(ConnectionError),
    stop=stop_after_attempt(DEFAULT_RETRY_ATTEMPTS),
    wait=wait_exponential(min=DEFAULT_RETRY_WAIT_MIN, max=DEFAULT_RETRY_WAIT_MAX),
    reraise=True,
)
def send_request(
    url: str,
    headers: dict[str, str],
    method: str = "GET",
    params: Optional[dict] = None,
    payload: Optional[Union[dict, str]] = None,
    timeout: int = DEFAULT_TIMEOUT,
    show_log: bool = False,
    fallback_urls: Iterable[str] | None = None,
    allowed_hosts: Iterable[str] | None = None,
) -> Any:
    """Central HTTP dispatcher with retry."""
    candidates = [url, *(fallback_urls or [])]
    last_error: ConnectionError | None = None

    for candidate in candidates:
        safe_url = sanitize_url(candidate, allowed_hosts=allowed_hosts)
        if show_log:
            logger.debug("%s %s", method.upper(), safe_url)
        try:
            return _do_request(safe_url, headers, method, params, payload, timeout)
        except ConnectionError as exc:
            last_error = exc
            if show_log:
                logger.warning("Provider request failed for %s: %s", safe_url, exc)

    if last_error is not None:
        raise last_error
    raise ConnectionError("No provider URL was supplied.")
