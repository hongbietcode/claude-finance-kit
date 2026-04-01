# Common Patterns & Gotchas

## Error Handling

```python
from claude_finance_kit import Stock
from claude_finance_kit.core.exceptions import (
    ClaudeFinanceKitError, ProviderError, InvalidSymbolError,
    DataNotFoundError, RateLimitError, SourceNotAvailableError,
)

try:
    df = Stock("FPT").quote.history(start="2024-01-01", end="2024-12-31")
    if df.empty:
        print("No data returned")
except InvalidSymbolError as e:
    print(f"Bad symbol: {e.details['symbol']}")
except RateLimitError:
    print("Rate limited — wait 30-60s and retry")
except ProviderError as e:
    print(f"Provider failed: {e.error_code} — {e.message}")
except ClaudeFinanceKitError as e:
    print(f"API error: {e}")
```

Always check `df.empty` before processing — API may return empty DataFrame without raising.

## Source Fallback (VCI → KBS)

```python
from claude_finance_kit import Stock
from claude_finance_kit.core.exceptions import ProviderError

def get_stock(symbol: str) -> Stock:
    try:
        s = Stock(symbol, source="VCI")
        df = s.quote.history(start="2024-01-01", end="2024-01-05")
        if df.empty:
            raise ValueError("empty")
        return s
    except (ProviderError, ValueError):
        return Stock(symbol, source="KBS")
```

VCI returns 403 on cloud environments (Colab, GitHub Actions, Codespaces) — always fallback to KBS.

## Caching

```python
import os
import pandas as pd
from claude_finance_kit import Stock

CACHE_DIR = ".cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def get_cached_history(symbol: str, start: str, end: str) -> pd.DataFrame:
    path = f"{CACHE_DIR}/{symbol}_{start}_{end}.parquet"
    if os.path.exists(path):
        return pd.read_parquet(path)
    df = Stock(symbol, source="KBS").quote.history(start=start, end=end)
    if not df.empty:
        df.to_parquet(path)
    return df
```

## Batch Multiple Symbols

```python
from claude_finance_kit import Stock

results = {}
for sym in ["VCB", "VNM", "FPT", "HPG"]:
    try:
        df = Stock(sym, source="KBS").quote.history(start="2024-01-01", end="2024-12-31")
        if not df.empty:
            results[sym] = df
    except Exception:
        continue
```

For large batches (50+ symbols), use the Collector instead:

```python
from claude_finance_kit.collector import run_ohlcv_task
run_ohlcv_task(["VCB", "VNM", "FPT"], start="2024-01-01", end="2024-12-31")
```

## TA with Price Data

```python
from claude_finance_kit import Stock
from claude_finance_kit.ta import Indicator

df = Stock("VCB", source="VCI").quote.history(start="2024-01-01", end="2024-12-31")
df = df.set_index('time')      # REQUIRED before Indicator()
ind = Indicator(df)
df['sma_20'] = ind.trend.sma(length=20)
df['rsi'] = ind.momentum.rsi(length=14)
df = df.join(ind.momentum.macd())
df = df.join(ind.trend.bbands(length=20))
```

## Fund ID Lookup

```python
from claude_finance_kit import Fund

fund = Fund()
row = fund.fund_filter(symbol="SSISCA")
fund_id = row['id'].iloc[0]      # string — pass to top_holding, nav_report, etc.
holdings = fund.top_holding(fund_id=fund_id)
```

## News Crawling

```python
from claude_finance_kit.news import Crawler, BatchCrawler

c = Crawler(site_name="cafef")
articles = c.get_latest_articles(limit=10)
detail = c.get_article_details(url=articles[0]['url'])

bc = BatchCrawler(site_name="cafef", request_delay=1.0)
batch = bc.fetch_articles(limit=100)
```

## Gotchas

1. Date format: always `YYYY-MM-DD`
2. No TCBS source — use VCI or KBS only
3. VCI 403: switch to KBS on cloud/CI environments
4. Intraday: max ~3 years back, trading hours only
5. Real-time data: only during 9:00-15:00 Vietnam time
6. DatetimeIndex: `Indicator()` requires `df.set_index('time')`
7. Empty data: always check `df.empty` before use
8. NaN warmup: TA indicators produce NaN for first N-1 rows
9. Fund ID: use `fund.fund_filter(symbol)['id'].iloc[0]` — not symbol directly
10. No auth needed: claude-finance-kit requires no API keys (except FMP for global stocks)
11. Intervals: use `"30m"`, `"1H"` (not `"30M"`, `"1h"`) — case-sensitive
12. News: `Crawler` and `BatchCrawler` are public exports; `NewsArticleParser`, `RSS`, `TrendingAnalyzer` require direct imports
