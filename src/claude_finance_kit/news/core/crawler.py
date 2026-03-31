"""Unified news crawler: fetches article lists via RSS or sitemap, then full content."""

from typing import Any, Dict, List, Optional, Union

from claude_finance_kit.news.config.sites import SITES_CONFIG
from claude_finance_kit.news.core.base import setup_logger
from claude_finance_kit.news.core.news_article_parser import NewsArticleParser
from claude_finance_kit.news.core.rss import RSS
from claude_finance_kit.news.core.sitemap import Sitemap
from claude_finance_kit.news.core.sitemap_resolver import DynamicSitemapResolver


class Crawler:
    """
    Unified crawler: fetches lists of links via RSS or sitemap,
    and retrieves detailed content via the article parser.
    """

    def __init__(
        self,
        site_name: Optional[str] = None,
        custom_config: Optional[Dict[str, Any]] = None,
        use_predefined_config: bool = True,
        debug: bool = False,
    ) -> None:
        """
        Parameters:
            site_name: Use a predefined site config from SITES_CONFIG.
            custom_config: Override config dynamically.
            use_predefined_config: Whether to use predefined config when site_name is provided.
            debug: Turn debug logging on/off.
        """
        self.logger = setup_logger(self.__class__.__name__, debug)
        self.debug = debug
        self.sitemap_resolver = DynamicSitemapResolver(debug=debug)

        if site_name and use_predefined_config:
            if site_name not in SITES_CONFIG:
                raise ValueError(f"Unsupported site: {site_name}")
            cfg = SITES_CONFIG[site_name]
            self.site_name = site_name
            self.rss_urls: List[str] = cfg.get("rss", {}).get("urls", [])
            self.parser_config: Dict[str, Any] = cfg.get("config", {})
            self.sitemap_url: Optional[str] = self._get_sitemap_url(site_name, cfg)

        elif custom_config:
            self.site_name = custom_config.get("site_name", "custom") if not site_name else site_name
            self.rss_urls = custom_config.get("rss_urls", [])
            self.parser_config = custom_config.get("config", {})
            self.sitemap_url = custom_config.get("sitemap_url")
            if not self.sitemap_url and "sitemap" in custom_config:
                self.sitemap_url = self.sitemap_resolver.get_sitemap_url(
                    self.site_name, custom_config
                )
        else:
            raise ValueError(
                "Either site_name with use_predefined_config=True or custom_config must be provided"
            )

    def _get_sitemap_url(self, site_name: str, config: Dict[str, Any]) -> Optional[str]:
        """Resolve the sitemap URL from config, handling dynamic patterns."""
        if "sitemap" in config:
            return self.sitemap_resolver.get_sitemap_url(site_name, config)
        return config.get("sitemap_url")

    def get_articles_from_feed(self, limit_per_feed: int = 10) -> List[Dict[str, Any]]:
        """Fetch article metadata only from RSS feeds."""
        if not self.rss_urls:
            raise ValueError("No RSS URLs configured")
        rss = RSS(site_name=self.site_name, show_log=self.debug)
        rss.rss_urls = self.rss_urls
        rows = rss.fetch()
        for row in rows:
            if "link" in row:
                row["url"] = row.pop("link")
        return rows[:limit_per_feed]

    def get_latest_articles(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch the latest article links from the sitemap."""
        if not self.sitemap_url:
            raise ValueError("No sitemap URL configured")
        sm = Sitemap(self.sitemap_url, show_log=self.debug)
        df = sm.run()
        return df.head(limit).to_dict("records")

    def get_articles(
        self,
        sitemap_url: Optional[Union[str, List[str]]] = None,
        limit: int = 10,
        limit_per_feed: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch articles: prefer RSS if available, fallback to sitemap.

        Parameters:
            sitemap_url: Override default sitemap URL(s).
            limit: Maximum total number of articles.
            limit_per_feed: Per-feed limit when multiple feeds are provided.
        """
        if self.rss_urls:
            self.logger.info("Fetching articles via RSS (preferred)")
            try:
                return self.get_articles_from_feed(limit_per_feed=limit)
            except Exception as exc:
                self.logger.warning(f"RSS fetch failed: {exc}. Trying sitemap as fallback...")

        if isinstance(sitemap_url, list):
            self.logger.info(f"Processing multiple sitemap URLs: {len(sitemap_url)} sources")
            results: List[Dict[str, Any]] = []
            per_feed = limit_per_feed if limit_per_feed is not None else limit
            for url in sitemap_url:
                try:
                    self.logger.info(f"Fetching from sitemap: {url} (limit per feed: {per_feed})")
                    sm = Sitemap(url, show_log=self.debug)
                    df = sm.run()
                    results.extend(df.head(per_feed).to_dict("records"))
                except Exception as exc:
                    self.logger.warning(f"Failed to fetch from {url}: {exc}")
            if results:
                return results[:limit]

        resolved_url = sitemap_url if isinstance(sitemap_url, str) else self.sitemap_url
        if resolved_url:
            self.logger.info(f"Fetching articles via Sitemap (fallback): {resolved_url}")
            try:
                sm = Sitemap(resolved_url, show_log=self.debug)
                df = sm.run()
                return df.head(limit).to_dict("records")
            except Exception as exc:
                self.logger.warning(f"Sitemap fetch failed: {exc}.")

        raise ValueError("No valid RSS or Sitemap source available for fetching articles.")

    def get_article_details(self, url: str) -> Dict[str, Any]:
        """Fetch full metadata and markdown content for a single article URL."""
        parser = NewsArticleParser(self.parser_config, show_log=self.debug)
        raw_html = parser.fetch_article(url)
        metadata = parser.parse(raw_html)
        metadata["markdown_content"] = parser.to_markdown(raw_html)
        metadata["url"] = url
        return metadata
