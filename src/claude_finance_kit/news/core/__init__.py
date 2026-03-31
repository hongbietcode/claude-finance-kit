"""News core module — crawlers, parsers, and feed readers."""

from claude_finance_kit.news.core.batch import BatchCrawler
from claude_finance_kit.news.core.crawler import Crawler
from claude_finance_kit.news.core.news_article_parser import NewsArticleParser
from claude_finance_kit.news.core.rss import RSS
from claude_finance_kit.news.core.sitemap import Sitemap
from claude_finance_kit.news.core.sitemap_resolver import DynamicSitemapResolver

__all__ = [
    "BatchCrawler",
    "Crawler",
    "NewsArticleParser",
    "RSS",
    "Sitemap",
    "DynamicSitemapResolver",
]
