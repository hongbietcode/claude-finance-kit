"""Shared HTTP client with retry and timeout support."""

import json
import logging
from typing import Any, Optional, Union

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



def _do_request(
    url: str,
    headers: dict[str, str],
    method: str,
    params: Optional[dict],
    payload: Optional[Union[dict, str]],
    timeout: int,
) -> dict[str, Any]:
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
        return response.json()

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
) -> dict[str, Any]:
    """Central HTTP dispatcher with retry."""
    if show_log:
        logger.debug("%s %s", method.upper(), url)
    return _do_request(url, headers, method, params, payload, timeout)
