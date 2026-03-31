# Stock Module

## Quick Start

```python
from claude_finance_kit import Stock

stock = Stock("FPT")                  # default source: VCI
stock = Stock("FPT", source="KBS")    # alternative source
```

Symbol is auto-uppercased. Source selects the data provider (see [Data Sources](#data-sources)).

## Sub-modules

### Quote (`stock.quote`)

| Method | Returns | Description |
|--------|---------|-------------|
| `history(start, end=None, interval="1D")` | `DataFrame` | OHLCV bars for the given date range |
| `intraday()` | `DataFrame` | Today's intraday tick data |
| `price_board(symbols=None)` | `DataFrame` | Current price snapshot for one or more symbols |

**`history` params:** `start` (str, `"YYYY-MM-DD"`, required), `end` (str or None, defaults to today), `interval` (str: `"1m"`, `"5m"`, `"15m"`, `"30m"`, `"1H"`, `"1D"`, `"1W"`, `"1M"`).

**`price_board` params:** `symbols` (list[str] or None) -- when `None`, uses the stock's own symbol.

### Company (`stock.company`)

| Method | Returns | Description |
|--------|---------|-------------|
| `overview()` | `DataFrame` | Company profile: name, industry, market cap, etc. |
| `shareholders()` | `DataFrame` | Major shareholder breakdown |
| `officers(**kwargs)` | `DataFrame` | Board members and executives |
| `news(limit=20, **kwargs)` | `DataFrame` | Company-specific news articles |
| `events(**kwargs)` | `DataFrame` | Corporate events (dividends, AGMs, etc.) |

### Finance (`stock.finance`)

| Method | Returns | Description |
|--------|---------|-------------|
| `balance_sheet(period="quarter")` | `DataFrame` | Assets, liabilities, equity |
| `income_statement(period="quarter")` | `DataFrame` | Revenue, expenses, net income |
| `cash_flow(period="quarter")` | `DataFrame` | Operating, investing, financing flows |
| `ratio(period="quarter")` | `DataFrame` | Financial ratios (PE, PB, ROE, etc.) |

All methods accept `period`: `"quarter"` or `"year"`.

### Listing (`stock.listing`)

| Method | Returns | Description |
|--------|---------|-------------|
| `all_symbols(exchange=None)` | `DataFrame` | All listed symbols |
| `symbols_by_group(group)` | `DataFrame` | Symbols in a market group |
| `symbols_by_industries()` | `DataFrame` | Industry classification for all symbols |

**`all_symbols` params:** `exchange` -- `"HOSE"`, `"HNX"`, `"UPCOM"`, or `None` for all.

**Common groups:** `"VN30"`, `"VN100"`, `"HNX30"`, `"VNMidCap"`, `"VNSmallCap"`.

### Trading (`stock.trading`)

| Method | Returns | Description |
|--------|---------|-------------|
| `price_depth()` | `DataFrame` | Order book with bid/ask price levels and volumes |

## Data Models

### `history()` → OHLCV DataFrame

Fields: `time` (datetime64), `open`, `high`, `low`, `close` (float64), `volume` (int64).

### `intraday()` → DataFrame

Fields: `time` (datetime64), `price` (float64), `volume` (int64), `match_type` (str: "BUY"/"SELL").

### `price_board()` → DataFrame (MultiIndex columns)

Two-level column structure: `(category, field)`.

| Category | Fields |
|----------|--------|
| **listing** | `organ_name`, `exchange`, `ceiling_price`, `floor_price`, `ref_price` |
| **bid_ask** | `bid_{1-3}_price`, `bid_{1-3}_volume`, `ask_{1-3}_price`, `ask_{1-3}_volume`, `total_bid_volume`, `total_ask_volume` |
| **match** | `match_price`, `match_volume`, `total_volume`, `total_value` |

### `overview()` → DataFrame

Fields: `symbol`, `id`, `issue_share`, `history`, `company_profile`, `icb_name2` (sector), `icb_name3` (industry), `icb_name4` (sub-sector), `financial_ratio_charter_capital`, `financial_ratio_issue_share`.

### `shareholders()` → DataFrame

Fields: `share_holder` (str), `quantity` (float), `share_own_percent` (float, 0-100), `update_date` (str).

### `officers()` → DataFrame

Fields: `officer_name`, `officer_position`, `officer_own_percent`, `quantity`, `update_date`, `position_short_name`.

### `news()` → DataFrame

Fields: `id`, `title`, `short_content`, `source_link`, `public_date`.

### `events()` → DataFrame

Fields: `id`, `event_title`, `event_list_name`, `event_list_code`, `public_date`, `issue_date`, `record_date`, `exright_date`, `ratio` (float), `value` (float), `source_url`.

### Financial statements (`balance_sheet`, `income_statement`, `cash_flow`) → DataFrame

Common fields: `symbol`, `year` (int), `period` (int: 1-4 for quarter, 0 for year), plus dynamic line-item columns (float, translated to English). All three share the same structure.

### `ratio()` → DataFrame

Common fields: `symbol`, `year`, `period`, plus: `Revenue`, `Revenue Growth`, `Net Profit`, `ROE`, `ROA`, `PE`, `PB`, `EPS`, `BVPS`, `Dividend`, and additional ratio columns.

### `all_symbols()` → DataFrame

Fields: `symbol`, `organ_name`.

### `symbols_by_group()` → Series

Returns `pd.Series` of ticker symbols in the requested group.

### `symbols_by_industries()` → DataFrame

Fields: `symbol`, `organ_name`, `icb_name2`, `icb_name3`, `icb_name4`, `com_type_code`, `icb_code1`..`icb_code4`.

### `price_depth()` → DataFrame

Fields: `price` (float), `acc_volume`, `acc_buy_volume`, `acc_sell_volume`, `acc_undefined_volume` (all float).

## Data Sources

| Source | Full Name | Notes |
|--------|-----------|-------|
| `"VCI"` | Vietnam Capital Investment | Default. Broadest VN stock API coverage. |
| `"KBS"` | KB Securities Vietnam | Alternative VN fallback provider. |
| `"MAS"` | Mirae Asset Securities | VN stocks — quote, financials, price depth. No company/listing. |
| `"TVS"` | Thien Viet Securities | VN stocks — company overview only. |
| `"VDS"` | Viet Dragon Securities | VN stocks — intraday only (auto-cookie). |
| `"BINANCE"` | Binance | Crypto (BTCUSDT, ETHUSDT). No API key required. |
| `"FMP"` | Financial Modeling Prep | Global stocks. Requires `FMP_API_KEY` env var or `api_key` kwarg. |

Source is set at construction and applies to all sub-module calls. FMP example: `Stock("AAPL", source="FMP", api_key="...")`.

## Examples

```python
from claude_finance_kit import Stock

# Historical prices and daily returns
df = Stock("FPT").quote.history(start="2024-01-01", end="2024-06-30")
df["daily_return"] = df["close"].pct_change()

# Company fundamentals
stock = Stock("VNM")
profile = stock.company.overview()
bs = stock.finance.balance_sheet(period="year")
income = stock.finance.income_statement(period="year")

# Screen VN30 stocks, fetch price board
vn30 = Stock("FPT").listing.symbols_by_group("VN30")
board = Stock("FPT").quote.price_board(symbols=vn30["symbol"].tolist())

# Quarterly financial ratios
ratios = Stock("HPG").finance.ratio(period="quarter")
print(ratios[["year_report", "length_report", "pe", "pb", "roe"]].tail(8))
```

**See also:** [`references/common-patterns.md`](../references/common-patterns.md) — error handling, source fallback, caching, batch processing, gotchas.
