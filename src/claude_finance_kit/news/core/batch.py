"""Batch crawler for fetching detailed articles from multiple sources with resume support."""

import os
from time import sleep
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from claude_finance_kit.news.core.base import setup_logger
from claude_finance_kit.news.core.crawler import Crawler

try:
    from tqdm import tqdm

    _TQDM_AVAILABLE = True
except ImportError:
    _TQDM_AVAILABLE = False


def _iter(iterable, desc: str):
    """Wrap iterable with tqdm progress bar if available."""
    if _TQDM_AVAILABLE:
        return tqdm(iterable, desc=desc)
    return iterable


class BatchCrawler:
    """
    Batch fetch detailed articles from multiple sources (RSS or sitemap),
    with optional resume via a temp file and configurable output path.
    """

    def __init__(
        self,
        site_name: Optional[str] = None,
        custom_config: Optional[Dict[str, Any]] = None,
        debug: bool = False,
        request_delay: float = 1.0,
        temp_file: str = "temp_articles.csv",
        output_path: Optional[str] = None,
    ) -> None:
        """
        Parameters:
            site_name: Predefined site to use.
            custom_config: User-defined config.
            debug: Turn debug logging on/off.
            request_delay: Seconds to sleep between requests.
            temp_file: Path for interim save.
            output_path: Path for final CSV output.
        """
        self.logger = setup_logger(self.__class__.__name__, debug)
        self.crawler = Crawler(site_name=site_name, custom_config=custom_config, debug=debug)
        self.request_delay = request_delay
        self.temp_file = temp_file
        self.output_path = output_path

    def _load_temp(self) -> pd.DataFrame:
        """Load interim DataFrame if it exists, else return empty DataFrame."""
        if os.path.exists(self.temp_file):
            try:
                return pd.read_csv(self.temp_file)
            except Exception:
                self.logger.warning("Could not load temp file, starting fresh")
        return pd.DataFrame()

    def _save_temp(self, df: pd.DataFrame) -> None:
        """Save interim DataFrame to CSV."""
        try:
            df.to_csv(self.temp_file, index=False)
        except Exception as exc:
            self.logger.error(f"Failed saving temp file: {exc}")

    def fetch_articles(
        self,
        sitemap_url: Optional[Union[str, List[str]]] = None,
        limit: int = 10,
        top_n: Optional[int] = None,
        top_n_per_feed: Optional[int] = None,
        within: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Fetch detailed articles from the configured source.

        Parameters:
            sitemap_url: Custom sitemap URL(s) to fetch articles from.
            limit: Maximum total number of articles.
            top_n: Alias for limit (backward compatibility).
            top_n_per_feed: Limit per feed when multiple feeds are provided.
            within: Reserved for future time-based filtering.
        """
        if top_n is not None:
            limit = top_n

        existing = self._load_temp()
        results: List[Dict[str, Any]] = []

        try:
            articles = self.crawler.get_articles(
                sitemap_url=sitemap_url,
                limit=limit,
                limit_per_feed=top_n_per_feed,
            )
            if not articles:
                self.logger.warning("No articles fetched from source.")
                return pd.DataFrame()
        except Exception as exc:
            self.logger.error(f"Failed fetching article metadata: {exc}")
            return pd.DataFrame()

        already_fetched = set(existing.get("url", pd.Series(dtype=str)).tolist())

        for article in _iter(articles, desc="Fetching article details"):
            url = article.get("link") or article.get("url")
            if not url:
                self.logger.warning("Article metadata missing 'url'. Skipping.")
                continue
            if url in already_fetched:
                self.logger.info(f"Skipping already fetched article: {url}")
                continue
            try:
                detail = self.crawler.get_article_details(url)
                results.append(detail)
                sleep(self.request_delay)
            except Exception as exc:
                self.logger.error(f"Failed fetching article detail {url}: {exc}")

        df = pd.DataFrame(results)

        if self.output_path and not df.empty:
            try:
                df.to_csv(self.output_path, index=False)
                self.logger.info(f"Saved output to {self.output_path}")
            except Exception as exc:
                self.logger.error(f"Failed saving output: {exc}")

        self._save_temp(df)
        return df

    def fetch_details_for_urls(self, urls: List[str]) -> pd.DataFrame:
        """
        Fetch detailed articles for a given list of URLs.

        Parameters:
            urls: List of article URLs to fetch details for.
        """
        existing = self._load_temp()
        already_fetched = set(existing.get("url", pd.Series(dtype=str)).tolist())
        results: List[Dict[str, Any]] = []

        for url in _iter(urls, desc="Fetching article details"):
            if url in already_fetched:
                self.logger.info(f"Skipping already fetched article: {url}")
                continue
            try:
                detail = self.crawler.get_article_details(url)
                results.append(detail)
                sleep(self.request_delay)
            except Exception as exc:
                self.logger.error(f"Failed fetching article detail {url}: {exc}")

        df = pd.DataFrame(results)

        if self.output_path and not df.empty:
            try:
                df.to_csv(self.output_path, index=False)
                self.logger.info(f"Saved output to {self.output_path}")
            except Exception as exc:
                self.logger.error(f"Failed saving output: {exc}")

        self._save_temp(df)
        return df
