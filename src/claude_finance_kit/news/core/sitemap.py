"""XML sitemap parser for Vietnamese financial news sites."""

from typing import Optional

import pandas as pd
import requests

from claude_finance_kit.news.config.const import DEFAULT_HEADERS
from claude_finance_kit.news.core.base import BaseParser

try:
    from bs4 import BeautifulSoup

    _BS4_AVAILABLE = True
except ImportError:
    _BS4_AVAILABLE = False


class Sitemap(BaseParser):
    """Parser for XML sitemaps into a DataFrame of URLs and optional lastmod dates."""

    def __init__(self, url: str, show_log: bool = False) -> None:
        """
        Parameters:
            url: The sitemap URL to download.
            show_log: Turn debug logging on/off.
        """
        super().__init__(show_log)
        self.url = url

    def fetch(self) -> str:
        """Download the sitemap XML as text."""
        self.logger.info(f"Fetching sitemap from {self.url}")
        resp = requests.get(self.url, headers=DEFAULT_HEADERS, timeout=30)
        resp.raise_for_status()
        return resp.text

    def parse(self, raw: str) -> pd.DataFrame:
        """Parse sitemap XML string into DataFrame with 'url' and optional 'lastmod'."""
        if not _BS4_AVAILABLE:
            raise ImportError("beautifulsoup4 is required: pip install beautifulsoup4")

        try:
            soup = BeautifulSoup(raw, "xml")
            entries = []
            for tag in soup.find_all("url"):
                loc = tag.find("loc")
                lastmod = tag.find("lastmod")
                if loc:
                    entry = {"url": loc.text.strip()}
                    if lastmod:
                        entry["lastmod"] = lastmod.text.strip()
                    entries.append(entry)

            if not entries:
                self.logger.warning("No URLs found in sitemap.")

            df = pd.DataFrame(entries)
            if "lastmod" in df.columns:
                df["lastmod"] = pd.to_datetime(df["lastmod"], errors="coerce")
                return df[["url", "lastmod"]]
            return df[["url"]] if not df.empty else pd.DataFrame(columns=["url", "lastmod"])
        except Exception as exc:
            self.logger.error(f"Failed to parse sitemap: {exc}")
            return pd.DataFrame(columns=["url", "lastmod"])

    def filter_by_date(
        self,
        df: pd.DataFrame,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> pd.DataFrame:
        """Filter DataFrame rows by lastmod between start and end dates."""
        if "lastmod" not in df.columns or df["lastmod"].isnull().all():
            return df
        df["lastmod"] = pd.to_datetime(df["lastmod"], errors="coerce").dt.tz_localize(None)
        if start:
            df = df[df["lastmod"] >= pd.Timestamp(start).tz_localize(None)]
        if end:
            df = df[df["lastmod"] <= pd.Timestamp(end).tz_localize(None)]
        return df
