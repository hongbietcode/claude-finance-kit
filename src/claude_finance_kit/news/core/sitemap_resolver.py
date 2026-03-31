"""Dynamic sitemap URL resolver for monthly and incremental sitemap patterns."""

import re
from datetime import datetime
from typing import Dict, Optional, Tuple

import requests

from claude_finance_kit.news.config.const import DEFAULT_HEADERS
from claude_finance_kit.news.core.base import setup_logger

try:
    from bs4 import BeautifulSoup

    _BS4_AVAILABLE = True
except ImportError:
    _BS4_AVAILABLE = False


class DynamicSitemapResolver:
    """Resolves sitemap URLs that change over time or follow incremental patterns."""

    def __init__(self, debug: bool = False) -> None:
        self.logger = setup_logger(self.__class__.__name__, debug)
        self._cache: Dict[str, Tuple[datetime, str]] = {}

    def get_sitemap_url(self, site_name: str, base_config: dict) -> Optional[str]:
        """
        Resolve the actual sitemap URL for a site based on its config pattern.

        Parameters:
            site_name: Name of the site.
            base_config: Site configuration dict.

        Returns:
            Resolved sitemap URL or None.
        """
        cache_key = f"{site_name}_sitemap"
        if cache_key in self._cache:
            cached_at, cached_url = self._cache[cache_key]
            if (datetime.now() - cached_at).total_seconds() < 3600:
                self.logger.debug(f"Using cached URL for {site_name}: {cached_url}")
                return cached_url

        sitemap_cfg = base_config.get("sitemap")
        if sitemap_cfg:
            pattern_type = sitemap_cfg.get("pattern_type")
            if pattern_type == "monthly":
                url = self._resolve_monthly(sitemap_cfg)
            elif pattern_type == "incremental":
                url = self._resolve_incremental(sitemap_cfg)
            else:
                url = sitemap_cfg.get("current_url")
        else:
            url = base_config.get("sitemap_url")

        if url:
            self._cache[cache_key] = (datetime.now(), url)
            return url

        self.logger.warning(f"No sitemap URL defined for {site_name}")
        return None

    def _resolve_monthly(self, sitemap_cfg: dict) -> str:
        """Resolve a sitemap URL following a monthly pattern."""
        now = datetime.now()
        base_url = sitemap_cfg.get("base_url", "")
        fmt = sitemap_cfg.get("format", "{year}-{month}")
        ext = sitemap_cfg.get("extension", "xml")
        date_part = fmt.format(year=now.year, month=now.month, day=now.day)
        return f"{base_url}{date_part}.{ext}"

    def _resolve_incremental(self, sitemap_cfg: dict) -> Optional[str]:
        """Resolve a sitemap URL using an incremental number from the sitemap index."""
        if not _BS4_AVAILABLE:
            self.logger.warning("beautifulsoup4 not available, using current_url fallback")
            return sitemap_cfg.get("current_url")

        index_url = sitemap_cfg.get("index_url")
        if not index_url:
            return sitemap_cfg.get("current_url")

        try:
            self.logger.debug(f"Checking sitemap index at {index_url}")
            resp = requests.get(index_url, headers=DEFAULT_HEADERS, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, "xml")
            candidates = []
            for tag in soup.find_all("sitemap"):
                loc = tag.find("loc")
                if loc and "post-sitemap" in loc.text:
                    candidates.append(loc.text)
            if candidates:
                latest = max(
                    candidates,
                    key=lambda x: int(re.search(r"post-sitemap(\d*)\.xml", x).group(1) or 0),
                )
                self.logger.info(f"Found latest sitemap: {latest}")
                return latest
        except Exception as exc:
            self.logger.error(f"Error resolving incremental sitemap from {index_url}: {exc}")

        return sitemap_cfg.get("current_url")
