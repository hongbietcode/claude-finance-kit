# API Reference — Stock & Company Data

## Stock (Core Entry Point)

```python
from claude_finance_kit import Stock

stock = Stock("FPT")           # defaults to source="VCI"
stock = Stock("FPT", source="KBS")  # explicit source
```

### Quote

```python
stock.quote.history(start="2025-01-01", end="2025-03-15", interval="1D")  # OHLCV DataFrame
stock.quote.intraday()                                                      # intraday ticks
stock.quote.price_board(symbols=["FPT", "VNM", "VCB"])                    # live price board
```

Intervals: 1m, 5m, 15m, 30m, 1H, 1D, 1W, 1M. Date format: YYYY-MM-DD.

#### price_board() — MultiIndex columns

Returns a DataFrame with **two-level MultiIndex columns** `(group, field)`. Access columns using tuples:

```python
df = stock.quote.price_board(symbols=["FPT", "VNM"])
df[("match", "match_price")]        # current price
df[("match", "open_price")]         # open price
df[("match", "highest")]            # high price
df[("match", "lowest")]             # low price
df[("match", "avg_match_price")]    # average price
df[("match", "accumulated_volume")] # total volume
df[("match", "accumulated_value")]  # total value
df[("match", "foreign_buy_volume")] # foreign buy
df[("match", "foreign_sell_volume")]# foreign sell
df[("listing", "symbol")]           # symbol
df[("listing", "exchange")]         # exchange
df[("listing", "ceiling")]          # ceiling price
df[("listing", "floor")]            # floor price
df[("listing", "ref_price")]        # reference price
df[("bid_ask", "bid_1_price")]      # best bid
df[("bid_ask", "ask_1_price")]      # best ask
```

**IMPORTANT:** Do NOT use flat column names like `df["match_price"]` — this will raise `KeyError`.

### Company

```python
stock.company.overview()            # name, industry, market_cap, P/E, P/B, etc. → DataFrame
stock.company.shareholders()        # major shareholders + ownership % → DataFrame
stock.company.officers()            # board members and officers → DataFrame
stock.company.news(limit=20)        # recent company news → DataFrame
stock.company.events()              # corporate events (dividends, AGM) → DataFrame
```

### Finance

```python
stock.finance.balance_sheet(period="quarter")     # or "year"
stock.finance.income_statement(period="quarter")
stock.finance.cash_flow(period="quarter")
stock.finance.ratio(period="quarter")             # ROE, ROA, EPS, P/E, P/B, etc.
```

### Listing

```python
stock.listing.all_symbols(exchange=None)          # all symbols; exchange: "HOSE","HNX","UPCOM"
stock.listing.symbols_by_group("VN30")            # VN30, VNMidCap, VNSmallCap, VNAllShare, etc.
stock.listing.symbols_by_industries()             # symbols grouped by industry → DataFrame
```

### Trading

```python
stock.trading.price_depth()    # bid/ask depth for the symbol → DataFrame
```

## Source Compatibility

| Source | Quote | Company | Finance | Listing | Trading |
|--------|-------|---------|---------|---------|---------|
| VCI | full | full | full | full | full |
| KBS | full | full | full | full | full |
| MAS | full | — | full | — | price_depth |
| TVS | — | overview | — | — | — |
| VDS | intraday | — | — | — | — |
| BINANCE | full | — | — | — | depth |
| FMP | full | overview+officers | full | — | — |

- Fallback: if VCI returns 403 (common on cloud IPs), switch to `Stock(symbol, source="KBS")`.
- FMP requires `FMP_API_KEY` env var or `Stock("AAPL", source="FMP", api_key="...")`.
- MAS covers VN stocks only. FMP covers global stocks (AAPL, MSFT, etc.).
