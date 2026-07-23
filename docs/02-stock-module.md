# Stock Module

## Quick Start

```python
from claude_finance_kit import Stock

stock = Stock("FPT")                  # default source: VCI
stock = Stock("FPT", source="KBS")    # alternative source
stock = Stock("FPT", market="VN", source="AUTO")
stock = Stock("AAPL", market="US", source="AUTO")
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

VCI normalizes ownership percentages to percentage points in the `0-100` range.
`officers(filter_by="working")` is the only supported status view; VCI REST
does not expose enough status metadata for `"resigned"` or `"all"`, so those
filters raise `NotImplementedError`.

### Finance (`stock.finance`)

| Method | Returns | Description |
|--------|---------|-------------|
| `balance_sheet(period="quarter", unit_multiplier=1)` | `DataFrame` | Assets, liabilities, equity |
| `income_statement(period="quarter", unit_multiplier=1)` | `DataFrame` | Revenue, expenses, net income |
| `cash_flow(period="quarter", unit_multiplier=1)` | `DataFrame` | Operating, investing, financing flows |
| `ratio(period="quarter")` | `DataFrame` | Financial ratios (PE, PB, ROE, etc.) |

All methods accept `period`: `"quarter"` or `"year"`. Financial statements also
accept a positive `unit_multiplier`; identifier columns such as `year` and `period`
are never scaled. KBS thousand-VND payloads are converted to VND before this
optional facade multiplier is applied. VCI and KBS use the same normalized
metric-column structure. Quarterly rows use `Q1`-`Q4`; annual rows use `FY`.

### Listing (`stock.listing`)

| Method | Returns | Description |
|--------|---------|-------------|
| `all_symbols(exchange=None)` | `DataFrame` | All listed symbols |
| `symbols_by_group(group)` | `DataFrame` | Symbols in a market group |
| `symbols_by_industries()` | `DataFrame` | Industry classification for all symbols |

**`all_symbols` params:** `exchange` -- `"HOSE"`, `"HNX"`, `"UPCOM"`, or `None` for all.

**Common groups and aliases:** `"VN30"`, `"VN100"`, `"VNALL"`, `"VNX50"`,
`"VNXALL"`, `"HNX30"`, `"HNXFIN"`, `"HNXCON"`, `"HNXLCAP"`, `"HNXMAN"`,
`"HNXMSCAP"`, `"UPCOMLAR"`, `"UPCOMMID"`, `"UPCOMSML"`.

### Trading (`stock.trading`)

| Method | Returns | Description |
|--------|---------|-------------|
| `price_depth()` | `DataFrame` | Order book with bid/ask price levels and volumes |
| `trades(start=None, end=None, limit=1000)` | `DataFrame` | Executed trades when supported |
| `order_book(start=None, end=None, limit=1000)` | `DataFrame` | Historical/latest bid-ask data |
| `foreign_flow(start=None, end=None)` | `DataFrame` | Foreign investor flow for VN symbols |
| `filings(limit=40)` | `DataFrame` | SEC filings for US symbols |

## Data Models

### `history()` → OHLCV DataFrame

Fields: `time` (datetime64), `open`, `high`, `low`, `close` (float64), `volume` (int64).

### `intraday()` → DataFrame

Fields: `time` (datetime64), `price` (float64), `volume` (int64), `match_type` (str: "BUY"/"SELL").

### `price_board()` → DataFrame

VCI uses two-level columns in the form `(category, field)`.

| Category | Fields |
|----------|--------|
| **listing** | `organ_name`, `exchange`, `ceiling`, `floor`, `ref_price` |
| **bid_ask** | `bid_{1-3}_price`, `bid_{1-3}_volume`, `ask_{1-3}_price`, `ask_{1-3}_volume`, `total_bid_volume`, `total_ask_volume` |
| **match** | `match_price`, `match_vol`, `accumulated_volume`, `accumulated_value`, `open_price`, `highest`, `lowest` |

KBS returns flat columns. Its accumulated and latest matched volumes are named
`volume_accumulated` and `volume_last`; the former `total_trades` name is no
longer emitted.

### `overview()` → DataFrame

Fields are provider-normalized to snake_case and typically include `symbol`,
`organ_name`, `organ_short_name`, `issue_share`, `company_profile`,
`market_cap`, `sector`, `sector_vn`, and `listing_date`. The exact extras vary
by provider response; fields available only from the retired GraphQL endpoint
are not guaranteed.

### `shareholders()` → DataFrame

Fields: `share_holder` (str), `quantity` (float), `share_own_percent` (float, 0-100), `update_date` (str).

### `officers()` → DataFrame

Fields: `officer_name`, `officer_position`, `officer_own_percent`,
`quantity`, `update_date`.

### `news()` → DataFrame

Fields: `id`, `title`, `short_content`, `source_link`, `public_date`.

### `events()` → DataFrame

Fields: `id`, `event_title`, `event_list_name`, `event_list_code`, `public_date`, `issue_date`, `record_date`, `exright_date`, `ratio` (float), `value` (float), `source_url`.

### Financial statements (`balance_sheet`, `income_statement`, `cash_flow`) → DataFrame

Common fields: `symbol`, `year` (int), `period` (`"Q1"`-`"Q4"` or
`"FY"`), plus dynamic normalized line-item columns (float). VCI and KBS
return the same row-per-period structure, and annual rows are emitted with
`period="FY"` for both providers.

### `ratio()` → DataFrame

Common fields: `symbol`, `year`, `period`, plus normalized snake-case
metrics such as `pe`, `pb`, `ps`, `roe`, `roa`, `roic`, `dividend_yield`,
`debt_to_equity`, `current_ratio`, and `gross_margin`.

### `all_symbols()` → DataFrame

Fields: `symbol`, `organ_name`.

### `symbols_by_group()` → Series

Returns `pd.Series` of ticker symbols in the requested group.

### `symbols_by_industries()` → DataFrame

Long-form fields: `symbol`, `organ_name`, `exchange`, `com_type_code`,
`icb_level` (1-4), `icb_code`, and `icb_name`.

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
| `"MSN"` | MSN Finance | Historical OHLCV only. Resolves provider SecId dynamically. |
| `"BINANCE"` | Binance | Crypto (BTCUSDT, ETHUSDT). No API key required. |
| `"FMP"` | Financial Modeling Prep | Global stocks. Requires `FMP_API_KEY` env var or `api_key` kwarg. |
| `"DNSE"` | DNSE OpenAPI | Official VN OHLCV, trades, bid/ask, foreign flow, instruments. |
| `"SSI"` | SSI FastConnect | Official VN OHLCV/listings/foreign flow plus entitlement-based stream. |
| `"ALPACA"` | Alpaca Market Data | US IEX bars, trades, quotes, snapshots, stream. |
| `"SEC"` | SEC EDGAR | US company metadata, filings, and XBRL facts. |

Source is set at construction and applies to all sub-module calls. Explicit
providers remain strict. `source="AUTO"` selects per method and requires
`market="VN"` or `market="US"` so ambiguous symbols cannot cross markets.
AUTO provenance is available through `DataFrame.attrs` and includes
`source`, `attempted_sources`, `market`, `fetched_at`, `data_timestamp`,
`delayed_seconds`, and `coverage`.

Authenticated AUTO providers accept isolated options:

```python
stock = Stock(
    "AAPL",
    market="US",
    source="AUTO",
    provider_options={
        "ALPACA": {"api_key": "...", "api_secret": "..."},
        "FMP": {"api_key": "..."},
    },
)
```

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
board = Stock("FPT").quote.price_board(symbols=vn30.tolist())

# Quarterly financial ratios
ratios = Stock("HPG").finance.ratio(period="quarter")
print(ratios[["year", "period", "pe", "pb", "roe"]].tail(8))
```
