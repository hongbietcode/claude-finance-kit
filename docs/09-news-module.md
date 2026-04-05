# News Module

Crawl Vietnamese financial news from 12+ sites with RSS and sitemap support.

**Install:** `pip install claude-finance-kit[news]`

## Quick Start

```python
from claude_finance_kit.news import Crawler, BatchCrawler

# Internal helpers (not in __all__, import directly):
from claude_finance_kit.news.core.news_article_parser import NewsArticleParser
from claude_finance_kit.news.core.rss import RSS
from claude_finance_kit.news.trending.analyzer import TrendingAnalyzer
```

## Crawler

Fetch articles from a single news site via RSS or sitemap.

```python
crawler = Crawler(site_name="cafef", debug=False)
```

### Supported Sites

| Site | Key | Sources |
|------|-----|---------|
| CafeF | `cafef` | Sitemap |
| CafeBiz | `cafebiz` | Sitemap + RSS |
| VietStock | `vietstock` | Sitemap + RSS |
| VnEconomy | `vneconomy` | Sitemap |
| PLO | `plo` | Sitemap |
| VnExpress | `vnexpress` | Sitemap + RSS |
| Tuoi Tre | `tuoitre` | Sitemap + RSS |
| KTSG | `ktsg` | Sitemap |
| NCDT | `ncdt` | Sitemap |
| DDDN | `dddn` | Sitemap |
| Bao Dau Tu | `baodautu` | Sitemap |
| Cong Thuong | `congthuong` | Sitemap + RSS |

### Fetch Articles

```python
crawler = Crawler(site_name="cafef")

articles = crawler.get_latest_articles(limit=10)
feed_articles = crawler.get_articles_from_feed(limit_per_feed=10)
combined = crawler.get_articles(limit=10)  # prefers RSS, fallback sitemap
```

`get_latest_articles()` uses sitemap. `get_articles_from_feed()` uses RSS feeds. `get_articles()` prefers RSS if available, falls back to sitemap.

### Get Full Article Content

Crawler provides a convenience method, or use `NewsArticleParser` directly:

```python
detail = crawler.get_article_details("https://cafef.vn/some-article.html")
print(detail["title"])
print(detail["markdown_content"])
```

For lower-level control, use `NewsArticleParser`:

```python
from claude_finance_kit.news.core.news_article_parser import NewsArticleParser

parser = NewsArticleParser(config=crawler.parser_config)
raw_html = parser.fetch_article("https://cafef.vn/some-article.html")
metadata = parser.parse(raw_html)
md = parser.to_markdown(raw_html, retain_links=True, retain_images=True)
```

### RSS Feed Reader

```python
from claude_finance_kit.news.core.rss import RSS

rss = RSS(site_name="cafef", description_format="text")
articles = rss.fetch()
```

## Custom Site Configuration

Crawl any site by providing a custom config.

```python
crawler = Crawler(custom_config={
    "site_name": "my_site",
    "rss_urls": ["https://example.com/rss.xml"],
    "sitemap_url": "https://example.com/sitemap.xml",
    "config": {
        "title_selector": {"class": "article-title"},
        "content_selector": {"tag": "div", "class": "article-body"},
        "short_desc_selector": {"class": "sapo"},
        "publish_time_selector": {"class": "publish-date"},
        "author_selector": {"class": "author-name"},
    },
})

articles = crawler.get_latest_articles(limit=5)
```

## BatchCrawler

Batch crawl with rate limiting and temp file support.

```python
from claude_finance_kit.news import BatchCrawler

bc = BatchCrawler(site_name="cafef", request_delay=1.0)
# Either site_name OR custom_config is required (cannot omit both)
articles = bc.fetch_articles(sitemap_url=None, limit=10, top_n=None, top_n_per_feed=None, within=None)
details = bc.fetch_details_for_urls(urls=["https://cafef.vn/article.htm"])
```

## TrendingAnalyzer

Extract trending topics from article text.

```python
from claude_finance_kit.news.trending.analyzer import TrendingAnalyzer

analyzer = TrendingAnalyzer(min_token_length=3)
analyzer.update_trends(text, ngram_range=None)
top = analyzer.get_top_trends(top_n=20)
```

## Data Models

### `crawler.get_articles_from_feed()` → list[dict]

| Field | Type | Description |
|-------|------|-------------|
| `url` | str | Article URL |
| `title` | str | Article headline |
| `description` | str | Short summary/excerpt |
| `publish_time` | str | Publication timestamp |

### `crawler.get_latest_articles()` → list[dict]

| Field | Type | Description |
|-------|------|-------------|
| `url` | str | Article URL |
| `lastmod` | str | Last modified timestamp |

### `crawler.get_article_details(url)` → dict

| Field | Type | Description |
|-------|------|-------------|
| `url` | str | Original article URL |
| `title` | str | Parsed article title |
| `short_description` | str | Short description/excerpt |
| `publish_time` | str | Publication date/time |
| `author` | str | Article author (if available) |
| `markdown_content` | str | Full article body as Markdown |

### Custom Config Selectors

| Selector Key | Description |
|-------------|-------------|
| `title_selector` | CSS class/tag for article title |
| `content_selector` | CSS tag + class for main content body |
| `short_desc_selector` | CSS class for article summary |
| `publish_time_selector` | CSS class for publication date |
| `author_selector` | CSS class for author name |

## Example Workflows

### Daily News Digest

```python
from claude_finance_kit.news import Crawler

sites = ["cafef", "vietstock", "baodautu"]
all_news = []

for site in sites:
    crawler = Crawler(site_name=site)
    articles = crawler.get_latest_articles(limit=5)
    all_news.extend(articles)

print(f"Collected {len(all_news)} articles from {len(sites)} sites")
```

### Full Article Extraction

```python
crawler = Crawler(site_name="vnexpress")
articles = crawler.get_latest_articles(limit=3)
for a in articles:
    detail = crawler.get_article_details(a["url"])
```

## Dependencies

Requires `[news]` extra: `pip install claude-finance-kit[news]`.

