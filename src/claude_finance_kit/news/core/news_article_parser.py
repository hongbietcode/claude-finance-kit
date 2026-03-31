"""Single news article HTML parser — extracts metadata and markdown content."""

from typing import Any, Dict, Optional

import requests

from claude_finance_kit.news.config.const import DEFAULT_HEADERS
from claude_finance_kit.news.core.base import BaseParser

try:
    from bs4 import BeautifulSoup

    _BS4_AVAILABLE = True
except ImportError:
    _BS4_AVAILABLE = False


class NewsArticleParser(BaseParser):
    """Parser for extracting metadata and content from a single news article."""

    def __init__(self, config: Dict[str, Any], show_log: bool = False) -> None:
        """
        Parameters:
            config: CSS selectors for title/content/short_desc/publish_time/author.
            show_log: Turn debug logging on/off.
        """
        super().__init__(show_log)
        self.config = config

    def fetch(self):
        """Not used directly — use fetch_article(url) instead."""
        raise NotImplementedError("Use fetch_article(url) instead")

    def fetch_article(self, url: str) -> str:
        """Download and return raw HTML for a given article URL."""
        self.logger.info(f"Fetching article HTML: {url}")
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=60)
        resp.raise_for_status()
        return resp.text

    def parse(self, raw_html: str) -> Dict[str, Optional[str]]:
        """Extract metadata fields from HTML string."""
        if not _BS4_AVAILABLE:
            raise ImportError("beautifulsoup4 is required: pip install beautifulsoup4")

        soup = BeautifulSoup(raw_html, "html.parser")

        def extract(selector: Optional[Dict[str, Any]]) -> Optional[str]:
            if not selector:
                return None
            tag = soup.find(
                selector.get("tag"),
                class_=selector.get("class"),
                id=selector.get("id"),
            )
            return tag.get_text(strip=True) if tag else None

        return {
            "title": extract(self.config.get("title_selector")),
            "short_description": extract(self.config.get("short_desc_selector")),
            "publish_time": extract(self.config.get("publish_time_selector")),
            "author": extract(self.config.get("author_selector")),
        }

    def to_markdown(
        self,
        raw_html: str,
        retain_links: bool = True,
        retain_images: bool = True,
    ) -> str:
        """Convert main article content block into Markdown."""
        if not _BS4_AVAILABLE:
            raise ImportError("beautifulsoup4 is required: pip install beautifulsoup4")

        try:
            import html2text
        except ImportError as exc:
            raise ImportError("html2text is required: pip install html2text") from exc

        soup = BeautifulSoup(raw_html, "html.parser")
        selector = self.config.get("content_selector")
        if not selector:
            raise ValueError("Missing 'content_selector' in config")

        content = soup.find(
            selector.get("tag"),
            class_=selector.get("class"),
            id=selector.get("id"),
        )
        if not content:
            raise ValueError("Article content block not found in HTML")

        converter = html2text.HTML2Text()
        converter.ignore_links = not retain_links
        converter.ignore_images = not retain_images
        return converter.handle(str(content))
