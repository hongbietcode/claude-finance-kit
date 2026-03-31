"""User-Agent string rotation and HTTP header construction utilities."""

import random
from typing import Optional

from claude_finance_kit._internal.browser_profiles import USER_AGENTS

DEFAULT_HEADERS: dict[str, str] = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,vi-VN;q=0.8,vi;q=0.7",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Cache-Control": "no-cache",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "DNT": "1",
    "Pragma": "no-cache",
    "sec-ch-ua-platform": '"Windows"',
    "sec-ch-ua-mobile": "?0",
}

HEADERS_MAPPING_SOURCE: dict[str, dict[str, str]] = {
    "SSI": {
        "Referer": "https://iboard.ssi.com.vn",
        "Origin": "https://iboard.ssi.com.vn",
    },
    "VND": {
        "Referer": "https://dchart.vndirect.com.vn",
        "Origin": "https://dchart.vndirect.com.vn",
    },
    "TCBS": {
        "Referer": "https://tcinvest.tcbs.com.vn/",
        "Origin": "https://tcinvest.tcbs.com.vn/",
    },
    "VCI": {
        "Referer": "https://trading.vietcap.com.vn/",
        "Origin": "https://trading.vietcap.com.vn/",
    },
    "MSN": {
        "Referer": "https://www.msn.com/",
        "Origin": "https://www.msn.com/",
    },
    "FMARKET": {
        "Referer": "https://fmarket.vn/",
        "Origin": "https://fmarket.vn/",
    },
    "SJC": {
        "Referer": "https://sjc.com.vn/bieu-do-gia-vang",
        "Origin": "https://sjc.com.vn",
    },
}

AUTH_SCHEMES: dict[str, str] = {
    "bearer": "Bearer",
    "basic": "Basic",
    "apikey": "ApiKey",
    "token": "Token",
    "jwt": "Bearer",
}


def get_random_user_agent() -> str:
    """Return a random User-Agent string from all available profiles."""
    browser = random.choice(list(USER_AGENTS.keys()))
    platform_name = random.choice(list(USER_AGENTS[browser].keys()))
    return USER_AGENTS[browser][platform_name]


def get_authorization_header(token: str, scheme: str = "Bearer") -> dict[str, str]:
    """Build an Authorization header for the given token and scheme."""
    auth_prefix = AUTH_SCHEMES.get(scheme.lower(), scheme)
    return {"Authorization": f"{auth_prefix} {token}"}


def merge_headers(*header_dicts: Optional[dict[str, str]]) -> dict[str, str]:
    """Merge multiple header dicts; later dicts override earlier ones."""
    result: dict[str, str] = {}
    for headers in header_dicts:
        if headers:
            result.update(headers)
    return result


def validate_headers(headers: dict[str, str]) -> dict[str, str]:
    """Strip None/empty values and coerce all keys/values to str."""
    return {str(k): str(v) for k, v in headers.items() if v is not None and v != ""}


def get_headers(
    data_source: str = "SSI",
    random_agent: bool = True,
    browser: str = "chrome",
    platform: str = "windows",
    authorization: Optional[str] = None,
    auth_scheme: str = "Bearer",
    custom_headers: Optional[dict[str, str]] = None,
    override_headers: Optional[dict[str, str]] = None,
    include_defaults: bool = True,
) -> dict[str, str]:
    """
    Build browser-like HTTP headers for a given data source.

    Priority (lowest to highest): defaults → source-specific → user-agent
    → referer/origin → authorization → custom_headers → override_headers.
    """
    headers: dict[str, str] = DEFAULT_HEADERS.copy() if include_defaults else {}

    source_config = HEADERS_MAPPING_SOURCE.get(data_source.upper(), {})
    source_headers = source_config.get("headers", {})
    if source_headers:
        headers.update(source_headers)

    if random_agent:
        ua = get_random_user_agent()
    else:
        ua = USER_AGENTS.get(browser.lower(), {}).get(platform.lower(), "")
        if not ua:
            ua = USER_AGENTS.get("chrome", {}).get("windows", "")

    if ua:
        headers["User-Agent"] = ua

    referer = source_config.get("Referer", "")
    origin = source_config.get("Origin", "")
    if referer:
        headers["Referer"] = referer
    if origin:
        headers["Origin"] = origin

    if authorization:
        headers.update(get_authorization_header(authorization, auth_scheme))

    if custom_headers:
        headers.update(custom_headers)

    if override_headers:
        headers.update(override_headers)

    return validate_headers(headers)
