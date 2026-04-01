# API Reference — Market, Macro, Fund & Commodity

## Market Valuation

```python
from claude_finance_kit import Market

market = Market("VNINDEX")        # or "HNX"
pe = market.pe(duration="5Y")     # "1Y", "2Y", "3Y", "5Y", "10Y", "15Y"
pb = market.pb(duration="5Y")

gainers   = market.top_gainer(limit=10)     # top gainers by % change
losers    = market.top_loser(limit=10)      # top losers by % change
liquidity = market.top_liquidity(limit=10)  # highest trading value
```

Returns DataFrame with date + ratio values. Source: VND.
Index options: VNINDEX, HNX, VN30.

## Macro (Vietnam Economics)

```python
from claude_finance_kit import Macro

macro = Macro()
macro.gdp(start="2023-01", end="2025-12", period="quarter")   # or "year"
macro.cpi(length="2Y", period="month")                         # or "quarter","year"
macro.interest_rate(start="2023-01-01", end="2025-12-31")      # daily pivot table
macro.exchange_rate(start="2023-01-01", end="2025-12-31")      # daily rates
macro.fdi(start="2023-01", end="2025-12", period="month")      # or "year"
macro.trade_balance(start="2023-01", end="2025-12", period="month")
```

Source: MBK (MayBank). All date params optional — omit for full history.

## Fund (Mutual Funds)

```python
from claude_finance_kit import Fund

fund = Fund()
fund.listing(fund_type="STOCK")       # "STOCK","BOND","BALANCED","" (all)
fund_id = fund.fund_filter(symbol="SSISCA")['id'].iloc[0]
fund.top_holding(fund_id=fund_id)     # top stocks in fund → DataFrame
fund.industry_holding(fund_id=fund_id)# sector allocation → DataFrame
fund.asset_holding(fund_id=fund_id)   # asset type breakdown → DataFrame
fund.nav_report(fund_id=fund_id)      # full NAV history → DataFrame
```

Note: use `fund_id` (string from `fund_filter`) — NOT `fundId`.
Source: FMARKET (58+ quỹ mở).

## Commodity

```python
from claude_finance_kit import Commodity

commodity = Commodity()
commodity.gold(length="1Y")           # Vietnamese + global gold prices
commodity.oil(length="1Y")            # crude oil + Vietnam gas prices
commodity.steel(length="1Y")          # steel HRC + iron ore
commodity.gas(length="1Y")            # natural gas + crude oil
commodity.fertilizer(length="1Y")     # urea fertilizer
commodity.agricultural(length="1Y")   # soybean, corn, sugar
```

All methods accept `start`, `end` (YYYY-MM-DD) or `length` ("1Y","6M","3M").
Source: SPL.
