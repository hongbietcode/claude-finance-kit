"""Proxy configuration, fetching, and rotation for HTTP requests."""

import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import requests

logger = logging.getLogger(__name__)

PROXYSCRAPE_API = "https://api.proxyscrape.com/v4/free-proxy-list/get"


@dataclass
class Proxy:
    """Represents a single proxy endpoint."""

    protocol: str
    ip: str
    port: int
    country: str = ""
    speed: float = 0.0
    last_checked: Optional[datetime] = None

    @property
    def address(self) -> str:
        return f"{self.protocol}://{self.ip}:{self.port}"

    @property
    def as_requests_dict(self) -> dict[str, str]:
        return {"http": self.address, "https": self.address}

    def __str__(self) -> str:
        return self.address


def _parse_proxy_list(raw: list[dict]) -> list[Proxy]:
    proxies: list[Proxy] = []
    for item in raw:
        try:
            protocol = item.get("protocol", item.get("Protocol", "http")).lower()
            if "ip" in item and "port" in item:
                ip, port = item["ip"], int(item["port"])
            elif "ip_data" in item:
                ip_data = item["ip_data"]
                ip, port = ip_data["ip"], int(ip_data["port"])
            elif "ipport" in item:
                ip, port_str = item["ipport"].split(":")
                port = int(port_str)
            else:
                full = item.get("proxy", "")
                if "://" in full:
                    protocol, rest = full.split("://", 1)
                    ip, port_str = rest.split(":")
                    port = int(port_str)
                else:
                    continue
            if not ip:
                continue
            proxies.append(
                Proxy(
                    protocol=protocol,
                    ip=ip,
                    port=port,
                    country=item.get("country", ""),
                    speed=float(item.get("speed", 0.0)),
                    last_checked=datetime.now(),
                )
            )
        except (ValueError, KeyError, AttributeError) as exc:
            logger.warning("Failed to parse proxy entry %s: %s", item, exc)
    return proxies


def fetch_free_proxies(limit: int = 15, timeout: int = 10) -> list[Proxy]:
    """Fetch free proxies from the proxyscrape public API."""
    params = {
        "request": "get_proxies",
        "skip": 0,
        "proxy_format": "protocolipport",
        "format": "json",
        "limit": min(limit, 100),
    }
    try:
        resp = requests.get(PROXYSCRAPE_API, params=params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        raw = data.get("proxies", [])
        if not isinstance(raw, list):
            logger.warning("proxyscrape returned unexpected payload")
            return []
        proxies = _parse_proxy_list(raw)
        logger.info("Fetched %d proxies from proxyscrape", len(proxies))
        return proxies
    except Exception as exc:
        logger.error("Failed to fetch proxies: %s", exc)
        return []


def test_proxy(proxy: Proxy, timeout: int = 5) -> bool:
    """Return True if the proxy can reach httpbin."""
    try:
        resp = requests.get(
            "https://httpbin.org/ip",
            proxies=proxy.as_requests_dict,
            timeout=timeout,
        )
        return resp.status_code == 200
    except Exception:
        return False


def parse_proxy_string(proxy_str: str) -> Optional[Proxy]:
    """Parse a proxy string like 'http://1.2.3.4:8080' into a Proxy object."""
    try:
        if "://" in proxy_str:
            protocol, rest = proxy_str.split("://", 1)
        else:
            protocol, rest = "http", proxy_str
        ip, port_str = rest.split(":")
        return Proxy(protocol=protocol, ip=ip, port=int(port_str))
    except Exception:
        logger.warning("Invalid proxy string: %s", proxy_str)
        return None


@dataclass
class ProxyPool:
    """Manages a pool of proxies with round-robin and random selection."""

    proxies: list[Proxy] = field(default_factory=list)
    _index: int = field(default=0, init=False, repr=False)

    @classmethod
    def from_strings(cls, proxy_strings: list[str]) -> "ProxyPool":
        parsed = [p for s in proxy_strings if (p := parse_proxy_string(s))]
        return cls(proxies=parsed)

    def next_round_robin(self) -> Optional[Proxy]:
        if not self.proxies:
            return None
        proxy = self.proxies[self._index % len(self.proxies)]
        self._index += 1
        return proxy

    def random(self) -> Optional[Proxy]:
        return random.choice(self.proxies) if self.proxies else None

    def first(self) -> Optional[Proxy]:
        return self.proxies[0] if self.proxies else None

    def reset(self) -> None:
        self._index = 0

    def as_address_list(self) -> list[str]:
        return [str(p) for p in self.proxies]
