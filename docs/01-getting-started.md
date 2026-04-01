# Getting Started

## Installation

Requires **Python 3.10+**.

```bash
pip install claude-finance-kit
```

Core dependencies installed automatically: `pandas`, `requests`, `pydantic`, `tenacity`.

### Optional Extras

Install additional modules as needed:

```bash
pip install claude-finance-kit[ta]        # Technical analysis (no extra deps)
pip install claude-finance-kit[collector]  # Batch data collector (duckdb, pyarrow, tqdm, aiohttp, websockets)
pip install claude-finance-kit[news]      # News crawlers (scipy, pyarrow)
pip install claude-finance-kit[search]    # Perplexity web search (perplexityai)
pip install claude-finance-kit[all]       # Everything above
```

---

## Quick Start

```python
from claude_finance_kit import Stock, Market, Macro, Fund, Commodity
from claude_finance_kit.search import PerplexitySearch
```

### Stock Data

Create a `Stock` instance for any Vietnamese ticker:

```python
stock = Stock("FPT")
```

**Quote** -- historical and intraday price data:

```python
df = stock.quote.history(start="2024-01-01")           # OHLCV DataFrame
df = stock.quote.history(start="2024-01-01", interval="1D")
df = stock.quote.intraday()                             # Today's intraday ticks
df = stock.quote.price_board()                          # Current price board
```

**Company** -- corporate information:

```python
info = stock.company.overview()       # DataFrame with company details
df   = stock.company.shareholders()   # Major shareholders DataFrame
df   = stock.company.officers()       # Board members and executives
df   = stock.company.news()           # Recent company news
df   = stock.company.events()         # Corporate events (dividends, etc.)
```

**Finance** -- financial statements:

```python
df = stock.finance.balance_sheet(period="quarter")
df = stock.finance.income_statement(period="year")
df = stock.finance.cash_flow(period="quarter")
df = stock.finance.ratio(period="quarter")
```

**Listing** -- symbol discovery:

```python
df = stock.listing.all_symbols()                # All listed symbols
df = stock.listing.all_symbols(exchange="HOSE") # Filter by exchange
df = stock.listing.symbols_by_group("VN30")     # Index constituents
df = stock.listing.symbols_by_industries()       # Sector classification
```

**Trading** -- order book:

```python
df = stock.trading.price_depth()   # Bid/ask depth
```

### Market Data

Track index-level metrics:

```python
market = Market("VNINDEX")

df = market.pe(duration="5Y")              # P/E ratio history
df = market.pb(duration="5Y")              # P/B ratio history
df = market.top_gainer(limit=10)           # Top gaining stocks
df = market.top_loser(limit=10)            # Top losing stocks
df = market.top_liquidity(limit=10)        # Most actively traded
```

### Macroeconomic Data

```python
macro = Macro()

df = macro.gdp(period="quarter")
df = macro.cpi(length="2Y", period="month")
df = macro.interest_rate()
df = macro.exchange_rate()
df = macro.fdi(period="month")
df = macro.trade_balance(period="month")
```

### Fund Data

```python
fund = Fund()

df = fund.listing()
df = fund.fund_filter("VFMVN30")
df = fund.top_holding(fund_id)
```

### Commodity Prices

```python
commodity = Commodity()

df = commodity.gold(length="1Y")
df = commodity.oil(length="1Y")
df = commodity.steel(length="1Y")
df = commodity.gas(length="1Y")
df = commodity.fertilizer(length="1Y")
df = commodity.agricultural(length="1Y")
```

---

## Optional Modules

These modules are lazy-loaded on first access and require their corresponding extras.

### Technical Analysis

No extra install needed beyond `[ta]`. Works with any OHLCV DataFrame.

```python
from claude_finance_kit.ta import Indicator

stock = Stock("FPT")
df = stock.quote.history(start="2024-01-01")

ind = Indicator(df)
sma = ind.trend.sma(20)
rsi = ind.momentum.rsi(14)
atr = ind.volatility.atr(14)
obv = ind.volume.obv()
```

### Collector

Requires `pip install claude-finance-kit[collector]`.

```python
from claude_finance_kit import collector
```

### News

Requires `pip install claude-finance-kit[news]`.

```python
from claude_finance_kit import news
```

### Search

Requires `pip install perplexityai` and `PERPLEXITY_API_KEY` env var.

```python
from claude_finance_kit.search import PerplexitySearch

search = PerplexitySearch()
results = search.search("FPT earnings Q1 2025")
results = search.search_multi(["VN30 outlook", "US Fed rate impact Vietnam"])
```

---

## Data Sources

Each module uses a default data provider. You can switch providers via the `source` parameter.

| Module    | Default Provider | Alternatives |
|-----------|-----------------|--------------|
| Stock     | VCI             | KBS, MAS, TVS, VDS, BINANCE, FMP |
| Market    | VND             | --           |
| Macro     | MBK             | --           |
| Fund      | FMARKET         | --           |
| Commodity | SPL             | --           |

```python
stock_vci = Stock("FPT")                # Uses VCI (default)
stock_kbs = Stock("FPT", source="KBS")  # Uses KBS instead
```

---

## Architecture Overview

- **Interface-first design**: User-facing modules (`Stock`, `Market`, `Macro`, `Fund`, `Commodity`) are thin facades that delegate to private `_provider/` implementations.
- **Return types**: All data methods return `pd.DataFrame` or `dict`.
- **Lazy loading**: Optional modules (`ta`, `collector`, `news`) are imported only on first access, keeping startup fast and avoiding unnecessary dependency requirements.
- **Provider registry**: Providers register themselves on import. The registry resolves the correct backend based on the `source` parameter.

```
claude_finance_kit/
  __init__.py          # Lazy-loading entry point
  core/                # Shared models, types, constants, exceptions
  stock/               # Stock facade (quote, company, finance, listing, trading)
  market/              # Market facade (PE, PB, top movers)
  macro/               # Macro facade (GDP, CPI, rates)
  commodity/           # Commodity facade (gold, oil, steel, gas)
  _internal/           # HTTP client, transforms, validation
  _provider/           # Provider implementations (VCI, KBS, VND, MBK, SPL, ...)
  ta/                  # Technical analysis indicators
  collector/            # Batch data collector and streaming
  news/                # News crawlers and trending analysis
  search/              # Perplexity web search client
```
