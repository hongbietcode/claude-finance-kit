"""RSS feed parser for Vietnamese financial news sites."""

from typing import Any, Dict, List, Optional

import pandas as pd
import requests

from claude_finance_kit.news.config.const import DEFAULT_HEADERS
from claude_finance_kit.news.config.sites import DEFAULT_RSS_MAPPING, SITES_CONFIG
from claude_finance_kit.news.core.base import BaseParser

try:
    from bs4 import BeautifulSoup

    _BS4_AVAILABLE = True
except ImportError:
    _BS4_AVAILABLE = False


class RSS(BaseParser):
    """Parser for RSS feeds into a DataFrame of articles."""

    def __init__(
        self,
        site_name: Optional[str] = None,
        description_format: str = "text",
        rss_url: Optional[str] = None,
        show_log: bool = False,
    ) -> None:
        """
        Parameters:
            site_name: Use predefined config if provided.
            description_format: 'text', 'html', or 'markdown'.
            rss_url: Custom RSS URL (overrides site_name).
            show_log: Turn debug logging on/off.
        """
        super().__init__(show_log)
        self.description_format = description_format.lower()
        self.rss_urls: List[str] = []
        self.mapping: Dict[str, str] = DEFAULT_RSS_MAPPING

        if site_name:
            site_cfg = SITES_CONFIG.get(site_name, {})
            rss_cfg = site_cfg.get("rss", {})
            self.rss_urls = rss_cfg.get("urls", [])
            self.mapping = rss_cfg.get("mapping", DEFAULT_RSS_MAPPING)
            self.logger.debug(f"Using RSS URLs from config: {self.rss_urls}")

        if rss_url:
            self.rss_urls = [rss_url]
            self.logger.debug(f"Manual RSS URL provided: {rss_url}")

        if not self.rss_urls:
            raise ValueError("No RSS feed URLs available")

        if self.description_format not in {"text", "html", "markdown"}:
            raise ValueError("description_format must be 'text', 'html', or 'markdown'")

    def fetch(self) -> List[Dict[str, Any]]:
        """Download each RSS URL and parse <item> tags into dicts."""
        if not _BS4_AVAILABLE:
            raise ImportError("beautifulsoup4 is required: pip install beautifulsoup4")

        results = []
        for url in self.rss_urls:
            try:
                self.logger.info(f"Fetching RSS feed: {url}")
                resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=10)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.content, "xml")
                for item in soup.find_all("item"):
                    entry: Dict[str, Any] = {}
                    for field, tag_name in self.mapping.items():
                        tag = item.find(tag_name)
                        if tag and tag.text:
                            value = tag.text.strip()
                            if field == "description":
                                value = self._format_description(value)
                            entry[field] = value
                    results.append(entry)
            except Exception as exc:
                self.logger.error(f"Error fetching RSS {url}: {exc}")
        return results

    def _format_description(self, raw: str) -> str:
        """Format description text according to description_format setting."""
        if self.description_format == "text":
            return BeautifulSoup(raw, "html.parser").get_text()
        if self.description_format == "markdown":
            try:
                import html2text

                converter = html2text.HTML2Text()
                converter.ignore_links = False
                return converter.handle(raw)
            except ImportError:
                self.logger.warning("html2text not installed, returning raw HTML")
        return raw

    def parse(self, raw: List[Dict[str, Any]]) -> pd.DataFrame:
        """Normalize list of dicts into a pandas DataFrame."""
        if not raw:
            return pd.DataFrame(columns=list(self.mapping.keys()))
        df = pd.DataFrame(raw)
        df = df.rename(columns=self.mapping)
        available = [c for c in self.mapping.values() if c in df.columns]
        return df[available]
