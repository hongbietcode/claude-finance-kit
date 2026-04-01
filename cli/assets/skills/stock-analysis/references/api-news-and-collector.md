# API Reference — News & Collector

## News (requires `claude-finance-kit[news]`)

### Crawlers

| Crawler | Speed | Use Case |
|---------|-------|----------|
| Crawler (RSS) | Fast (<10s) | Latest articles, monitoring |
| BatchCrawler | Sync | History, simple batch |

### Usage

```python
from claude_finance_kit.news import Crawler, BatchCrawler

c = Crawler(site_name="cafef")
articles = c.get_latest_articles(limit=10)
feed = c.get_articles_from_feed(limit_per_feed=20)
combined = c.get_articles(limit=10)       # prefers RSS, fallback sitemap
detail = c.get_article_details(url=articles[0]['url'])

bc = BatchCrawler(site_name="cafef", request_delay=1.0)
batch = bc.fetch_articles(limit=100, top_n=None, top_n_per_feed=None, within=None)
details_df = bc.fetch_details_for_urls(urls=["https://cafef.vn/article-1.htm"])
```

#### Internal helpers (not in `__all__`, import directly)

```python
from claude_finance_kit.news.core.news_article_parser import NewsArticleParser
from claude_finance_kit.news.core.rss import RSS
from claude_finance_kit.news.trending.analyzer import TrendingAnalyzer

parser = NewsArticleParser(config=c.parser_config)
raw_html = parser.fetch_article(url=articles[0]['url'])
metadata = parser.parse(raw_html)
md = parser.to_markdown(raw_html, retain_links=True, retain_images=True)

rss = RSS(site_name="cafef", description_format="text")
rss_articles = rss.fetch()

analyzer = TrendingAnalyzer(min_token_length=3)
analyzer.update_trends(text, ngram_range=None)
top = analyzer.get_top_trends(top_n=20)
```

### Output

Article list items: `url, title, description, publish_time`.
`get_article_details` returns: `title, short_description, publish_time, author, markdown_content, url`.
`fetch_details_for_urls` returns: DataFrame with same columns for multiple URLs.

### Supported Sites

cafef, cafebiz, vietstock, vneconomy, plo, vnexpress, tuoitre, ktsg, ncdt, dddn, baodautu, congthuong

### Gotchas

- Add `request_delay=1.0+` to avoid IP blocking
- RSS = latest 1-2 weeks; sitemap = 1-2 years history
- If 429 error, wait 1-2 hours before retrying
- Content may contain HTML — strip manually if needed

## Collector (requires `claude-finance-kit[collector]`)

### Quick Start

```python
from claude_finance_kit.collector import OHLCVTask, run_ohlcv_task

run_ohlcv_task(["VCB", "ACB", "HPG"], start="2024-01-01", end="2024-12-31", interval="1D")

task = OHLCVTask(base_path="./data/ohlcv")
task.run(["VCB", "ACB", "HPG"], start="2024-01-01", end="2024-12-31", interval="1D")
```

Output: `./data/ohlcv/{symbol}.csv`

### Built-in Tasks

| Task | Import | Function |
|------|--------|----------|
| OHLCV | `OHLCVTask` / `run_ohlcv_task` | `run(tickers, **fetch_kwargs)` / `run_ohlcv_task(tickers, start, end, interval)` |
| Financial | `FinancialTask` / `run_financial_task` | `run(tickers, **fetch_kwargs)` / `run_financial_task(tickers, ...)` |
| Intraday | `IntradayTask` / `run_intraday_task` | `run(tickers, mode="eod"|"live", interval=60, backup=True)` / `run_intraday_task(tickers, mode, interval, backup, max_backups)` |

### Exporters

```python
from claude_finance_kit.collector import CSVExporter, ParquetExporter, DuckDBExporter, TimeSeriesExporter

CSVExporter(base_path="/tmp/data").export(df, ticker="VCB")
ParquetExporter(base_path="/tmp/data", data_type="ohlcv").export(df, ticker="VCB")
DuckDBExporter(db_path="/tmp/data.duckdb").export(df, ticker="VCB")
TimeSeriesExporter(base_path="/tmp/data", file_format="parquet").export(
    df,
    ticker="VCB",
    data_type="intraday",
    deduplicate=True,
)
```

### Custom Collector

```python
from typing import Any

from claude_finance_kit.collector import (
    CSVExporter,
    DataFrameValidator,
    DeduplicatingTransformer,
    Scheduler,
    StockFetcher,
)


class QuoteHistoryFetcher(StockFetcher):
    def _call(self, ticker: str, **kwargs: Any):
        from claude_finance_kit import Stock

        return Stock(ticker).quote.history(
            start=kwargs.get("start", "2024-01-01"),
            end=kwargs.get("end", "2024-12-31"),
            interval=kwargs.get("interval", "1D"),
        )


fetcher = QuoteHistoryFetcher()
validator = DataFrameValidator()
validator.required_columns = ["time", "open", "high", "low", "close", "volume"]
transformer = DeduplicatingTransformer()
exporter = CSVExporter(base_path="/tmp/custom-collector")

scheduler = Scheduler(fetcher, validator, transformer, exporter,
                      retry_attempts=3, backoff_factor=2.0, max_workers=3,
                      request_delay=0.5, rate_limit_wait=35.0)
scheduler.process_ticker("VCB", fetcher_kwargs={"start": "2024-01-01", "end": "2024-12-31"})
scheduler.run(tickers=["VCB", "ACB"], fetcher_kwargs={"start": "2024-01-01", "end": "2024-12-31"})
```

Architecture: `Input → Fetcher → Validator → Transformer → Exporter → Output`

### Stream (WebSocket)

```python
from claude_finance_kit.collector.stream import BaseWebSocketClient, expand_data_type_group, validate_data_types
```

### Scheduler Tuning

| Scale | max_workers | request_delay |
|-------|-------------|---------------|
| <50 tickers | 3 | 0.5s |
| 100-300 | 2 | 1.0s |
| 500+ | 1 | 2.0s |

---

## Perplexity Search

Web search via Perplexity API. Requires `pip install perplexityai` and `PERPLEXITY_API_KEY` env var.

### Usage

```python
from claude_finance_kit.search import PerplexitySearch

search = PerplexitySearch()
# or with explicit config
search = PerplexitySearch(api_key="...", country="VN", max_results=10, max_tokens_per_page=1024, debug=False)
```

### Methods

#### `search(query, max_results=None, domain_filter=None, language_filter=None) → List[dict]`

Single query search.

```python
results = search.search("FPT earnings Q1 2025")
results = search.search("kinh tế vĩ mô Việt Nam lãi suất 2025")
results = search.search(
    "US Fed rate decision impact on Vietnam",
    max_results=5,
    domain_filter=["reuters.com", "bloomberg.com"],
    language_filter=["en"],
)
```

**Parameters:**
- `query` (str) — Any search query string
- `max_results` (int, optional) — Override default limit (default: 10)
- `domain_filter` (List[str], optional) — Allowlist/denylist domains (prefix `-` to exclude)
- `language_filter` (List[str], optional) — ISO 639-1 codes, e.g. `["vi", "en"]`

**Returns:** `List[dict]` — Each dict has keys: `title`, `url`, `snippet`, `date`

#### `search_multi(queries, max_results_each=5) → List[dict]`

Batch up to 5 queries in one API request.

```python
results = search.search_multi(["VN30 outlook 2025", "FPT vs VNM comparison"])
```

**Parameters:**
- `queries` (List[str]) — 1-5 query strings
- `max_results_each` (int) — Results per query (default: 5)

**Returns:** Flat `List[dict]` across all queries

### Data Models

```python
from claude_finance_kit.search.models import SearchResult, SearchResponse

# SearchResult: title, url, snippet, date (optional)
# SearchResponse: query, results → .to_dict_list()
```

### Gotchas

- Requires `PERPLEXITY_API_KEY` env var or `api_key=` parameter
- `perplexityai` package must be installed separately (`pip install perplexityai`)
- `search_multi` supports at most 5 queries per request — raises `ValueError` if exceeded
- Default country is `"VN"` — set `country` param for other regions
