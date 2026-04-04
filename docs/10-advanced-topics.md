# Advanced Topics

Provider system, error handling, type system, and configuration.

## Provider Architecture

All user-facing modules delegate to private providers via a registry pattern.

```
Stock("FPT") → registry.get_stock("VCI") → VCIProvider → API calls
Market()     → registry.get_market("VND") → VNDProvider → API calls
```

### 6 Provider Types

| Type | ABC | Default | Facade |
|------|-----|---------|--------|
| Stock | `StockProvider` | VCI | `Stock` |
| Market | `MarketProvider` | VND | `Market` |
| Macro | `MacroProvider` | MBK | `Macro` |
| Fund | `FundProvider` | FMARKET | `Fund` |
| Commodity | `CommodityProvider` | SPL | `Commodity` |
| Stream | `StreamProvider` | — | Pipeline |

### Provider Registry

```python
from claude_finance_kit._provider._registry import ProviderRegistry

registry = ProviderRegistry()
registry.list_sources(provider_type="stock")
```

The registry is a singleton with `register_*/get_*` methods for stock, market, macro, fund, commodity, stream.

### Switching Data Sources

```python
from claude_finance_kit import Stock, Market

stock_vci = Stock("FPT", source="VCI")
stock_kbs = Stock("FPT", source="KBS")

market = Market("VNINDEX", source="VND")
```

### Available Sources

| Source | Type | Description |
|--------|------|-------------|
| VCI | Stock | Vietnam Capital Investment (default) — full coverage |
| KBS | Stock | KB Securities Vietnam — full coverage |
| MAS | Stock | Mirae Asset Securities — quote, financials, price depth |
| FMP | Stock | Financial Modeling Prep — global stocks, requires API key |
| VND | Market | VNDirect |
| MBK | Macro | MBBank economics data |
| FMARKET | Fund | FMarket fund platform |
| SPL | Commodity | Simplize commodity data |
| TVS | Stock | Thien Viet Securities — company overview only |
| VDS | Stock | Viet Dragon Securities — intraday only (auto-cookie) |
| BINANCE | Stock | Crypto — history, intraday, depth (no API key required) |

## Error Handling

All exceptions inherit from `ClaudeFinanceKitError`.

```python
from claude_finance_kit.core.exceptions import (
    ClaudeFinanceKitError,
    ProviderError,
    InvalidSymbolError,
    DataNotFoundError,
    RateLimitError,
    SourceNotAvailableError,
    InvalidDateRangeError,
)
```

### Exception Hierarchy

```
ClaudeFinanceKitError (base)
├── ProviderError          # Provider API failures
├── InvalidSymbolError     # Invalid ticker symbol
├── DataNotFoundError      # No data for query
├── RateLimitError         # API rate limit hit
├── SourceNotAvailableError # Unknown data source
└── InvalidDateRangeError  # Bad date range
```

### Usage

```python
from claude_finance_kit import Stock
from claude_finance_kit.core.exceptions import InvalidSymbolError, ProviderError

try:
    stock = Stock("INVALID_SYMBOL")
    df = stock.quote.history(start="2024-01-01")
except InvalidSymbolError as e:
    print(f"Bad symbol: {e.details['symbol']}")
except ProviderError as e:
    print(f"Provider failed: {e.error_code} - {e.message}")
```

Each exception has:
- `message` — Human-readable description
- `error_code` — Machine-readable code (e.g., `SYMBOL_001`, `NETWORK_429`)
- `details` — Dict with contextual info
- `to_dict()` — Serialize to dict

## Type System

```python
from claude_finance_kit.core.types import Interval, Exchange, AssetType, DataSource
```

| Enum | Values |
|------|--------|
| `Interval` | `MINUTE_1`, `MINUTE_5`, `MINUTE_15`, `MINUTE_30`, `HOUR_1`, `DAY_1`, `WEEK_1`, `MONTH_1` |
| `Exchange` | `HOSE`, `HNX`, `UPCOM` |
| `AssetType` | `STOCK`, `ETF`, `BOND`, `DERIVATIVE`, `FUND`, `INDEX`, `FOREX`, `CRYPTO`, `COMMODITY` |
| `DataSource` | `all_sources()` → `['VCI', 'KBS', 'MAS', 'TVS', 'VND', 'VDS', 'CAFEF', 'FMARKET', 'SPL', 'MBK', 'MSN', 'DNSE', 'SSI', 'FMP', 'BINANCE']` |

## Lazy Loading

Optional modules load on first access, keeping base import instant.

```python
import claude_finance_kit          # fast — only pandas, requests, pydantic, tenacity
claude_finance_kit.ta              # loads TA module on first access
claude_finance_kit.collector       # loads collector module (requires [collector] extra)
claude_finance_kit.news            # loads news module (requires [news] extra)
```

## Configuration

### HTTP Client

- Auto-retry with exponential backoff (tenacity)
- Random user-agent rotation to avoid blocks
- Configurable timeouts

### Data Models

Pydantic v2 models for structured data:

```python
from claude_finance_kit.core.models import StockInfo, DateRange

info = StockInfo(symbol="FPT", exchange="HOSE", name="FPT Corporation")
dates = DateRange(start="2024-01-01", end="2024-12-31")
```

## Constants

```python
from claude_finance_kit.core.constants import INDICES_INFO, INDICES_MAP, INDEX_GROUPS, SECTOR_IDS, EXCHANGES
```

