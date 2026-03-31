"""Shared HTTP client with retry, timeout, and proxy support."""

import json
import logging
from enum import Enum
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


class ProxyMode(str, Enum):
    TRY = "try"
    ROTATE = "rotate"
    RANDOM = "random"
    SINGLE = "single"


class RequestMode(str, Enum):
    DIRECT = "direct"
    PROXY = "proxy"


_rotate_index: int = 0


def _build_proxy_dict(proxy_url: str) -> dict[str, str]:
    return {"http": proxy_url, "https": proxy_url}


def _select_proxy(proxy_list: list[str], mode: ProxyMode) -> str:
    global _rotate_index
    if not proxy_list:
        raise ValueError("proxy_list is empty.")
    if mode == ProxyMode.SINGLE:
        return proxy_list[0]
    if mode == ProxyMode.RANDOM:
        import random
        return random.choice(proxy_list)
    if mode == ProxyMode.ROTATE:
        proxy = proxy_list[_rotate_index % len(proxy_list)]
        _rotate_index += 1
        return proxy
    return proxy_list[0]


def reset_proxy_rotation() -> None:
    """Reset round-robin proxy index to 0."""
    global _rotate_index
    _rotate_index = 0


def _do_request(
    url: str,
    headers: dict[str, str],
    method: str,
    params: Optional[dict],
    payload: Optional[Union[dict, str]],
    timeout: int,
    proxies: Optional[dict[str, str]],
) -> dict[str, Any]:
    """Execute a single HTTP request and return parsed JSON."""
    try:
        if method.upper() == "GET":
            response = requests.get(
                url, headers=headers, params=params, timeout=timeout, proxies=proxies
            )
        else:
            if isinstance(payload, dict):
                body = json.dumps(payload)
            elif isinstance(payload, str):
                body = payload
            else:
                body = None
            response = requests.post(
                url, headers=headers, data=body, timeout=timeout, proxies=proxies
            )

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
    proxy_list: Optional[list[str]] = None,
    proxy_mode: Union[ProxyMode, str] = ProxyMode.TRY,
    request_mode: Union[RequestMode, str] = RequestMode.DIRECT,
    show_log: bool = False,
) -> dict[str, Any]:
    """
    Central interface for all HTTP request modes.

    Retries up to DEFAULT_RETRY_ATTEMPTS times on ConnectionError using
    exponential back-off (tenacity).  Supports direct and proxy request modes.

    Args:
        url: Endpoint URL.
        headers: HTTP headers dict.
        method: 'GET' or 'POST'.
        params: Query parameters (GET).
        payload: Request body (POST); dict or raw string.
        timeout: Per-request timeout in seconds.
        proxy_list: List of proxy URL strings for PROXY mode.
        proxy_mode: How to pick a proxy from proxy_list.
        request_mode: DIRECT (no proxy) or PROXY.
        show_log: Emit debug-level log lines for each request.

    Returns:
        Parsed JSON response as a dict.

    Raises:
        ConnectionError: After all retry attempts are exhausted.
        ValueError: For invalid enum values or missing proxy_list in PROXY mode.
    """
    if isinstance(proxy_mode, str):
        proxy_mode = ProxyMode(proxy_mode)
    if isinstance(request_mode, str):
        request_mode = RequestMode(request_mode)

    if show_log:
        logger.debug("%s %s (mode=%s)", method.upper(), url, request_mode.value)

    if request_mode == RequestMode.PROXY:
        if not proxy_list:
            raise ValueError("proxy_list is required for PROXY mode.")

        if proxy_mode == ProxyMode.TRY:
            last_exc: Exception = ConnectionError("No proxies available.")
            for proxy_url in proxy_list:
                try:
                    if show_log:
                        logger.debug("Trying proxy: %s", proxy_url)
                    return _do_request(
                        url, headers, method, params, payload,
                        timeout, _build_proxy_dict(proxy_url),
                    )
                except ConnectionError as exc:
                    last_exc = exc
            raise ConnectionError(f"All proxies failed. Last: {last_exc}") from last_exc

        selected = _select_proxy(proxy_list, proxy_mode)
        if show_log:
            logger.debug("Using proxy (%s): %s", proxy_mode.value, selected)
        return _do_request(
            url, headers, method, params, payload,
            timeout, _build_proxy_dict(selected),
        )

    return _do_request(url, headers, method, params, payload, timeout, proxies=None)


def send_direct(
    url: str,
    headers: dict[str, str],
    **kwargs: Any,
) -> dict[str, Any]:
    """Convenience wrapper: send a direct (no-proxy) request."""
    return send_request(url, headers, request_mode=RequestMode.DIRECT, **kwargs)


def send_via_proxy(
    url: str,
    headers: dict[str, str],
    proxy_list: list[str],
    **kwargs: Any,
) -> dict[str, Any]:
    """Convenience wrapper: send a request through the provided proxy list."""
    return send_request(
        url, headers, proxy_list=proxy_list,
        request_mode=RequestMode.PROXY, **kwargs,
    )
