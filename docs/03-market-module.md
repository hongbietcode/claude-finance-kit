# Market Module

The `Market` class provides index-level data for Vietnamese stock market indices, including valuation ratios and daily top movers.

## Quick Start

```python
from claude_finance_kit import Market

market = Market("VNINDEX")
market = Market("HNX30", source="VND")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `index` | str | `"VNINDEX"` | Index symbol: `"VNINDEX"`, `"HNX30"`, `"VN30"`, etc. |
| `source` | str | `"VND"` | Data source identifier |

## Methods

All methods return a `pd.DataFrame`.

### pe(duration)

Historical P/E ratio for the index.

```python
pe_data = market.pe(duration="5Y")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `duration` | str | `"5Y"` | Lookback period: `"1Y"`, `"2Y"`, `"3Y"`, `"5Y"`, `"10Y"`, `"15Y"` |

### pb(duration)

Historical P/B ratio for the index.

```python
pb_data = market.pb(duration="3Y")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `duration` | str | `"5Y"` | Lookback period: `"1Y"`, `"2Y"`, `"3Y"`, `"5Y"`, `"10Y"`, `"15Y"` |

### top_gainer(limit)

Stocks with the highest price increase on the exchange today.

```python
gainers = market.top_gainer(limit=10)
```

### top_loser(limit)

Stocks with the largest price decline on the exchange today.

```python
losers = market.top_loser(limit=10)
```

### top_liquidity(limit)

Most actively traded stocks by trading value.

```python
liquid = market.top_liquidity(limit=10)
```

All three top-mover methods accept:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | `10` | Number of stocks to return |

## Data Models

### `market.pe()` → DataFrame

| Field | Type | Description |
|-------|------|-------------|
| `reportDate` | datetime64 (index) | Date of the report |
| `pe` | float | Price-to-Earnings ratio for the index |

### `market.pb()` → DataFrame

| Field | Type | Description |
|-------|------|-------------|
| `reportDate` | datetime64 (index) | Date of the report |
| `pb` | float | Price-to-Book ratio for the index |

### `market.top_gainer()` / `top_loser()` / `top_liquidity()` → DataFrame

| Field | Type | Description |
|-------|------|-------------|
| `symbol` | str | Ticker symbol |
| `index` | str | Market index (VNIndex, HNX, VN30) |
| `last_price` | float | Last traded price |
| `last_updated` | str | Timestamp of last update |
| `price_change_1d` | float | Absolute price change (1 day) |
| `price_change_pct_1d` | float | Percentage price change (1 day) |
| `accumulated_value` | float | Total traded value (VND) |
| `avg_volume_20d` | float | 20-day average volume |

## Examples

### Compare P/E Across Indices

```python
from claude_finance_kit import Market

indices = ["VNINDEX", "HNX30", "VN30"]
pe_frames = {}

for idx in indices:
    m = Market(idx)
    pe_frames[idx] = m.pe(duration="3Y")

for name, df in pe_frames.items():
    latest = df.iloc[-1]
    print(f"{name}: P/E = {latest['pe']:.2f}")
```

### Daily Market Movers Report

```python
market = Market("VNINDEX")

gainers = market.top_gainer(limit=5)
losers = market.top_loser(limit=5)
liquid = market.top_liquidity(limit=5)

print("=== Top Gainers ===")
print(gainers[["symbol", "price", "change_pct"]].to_string(index=False))

print("\n=== Top Losers ===")
print(losers[["symbol", "price", "change_pct"]].to_string(index=False))

print("\n=== Most Liquid ===")
print(liquid[["symbol", "value"]].to_string(index=False))
```

### P/E and P/B Side by Side

```python
market = Market("VN30")

pe = market.pe(duration="1Y")
pb = market.pb(duration="1Y")

merged = pe.merge(pb, on="date", suffixes=("_pe", "_pb"))
print(merged.tail(10))
```

## Notes

- Index symbols are case-insensitive internally but conventionally uppercase.
- Top mover methods reflect intraday or end-of-day data depending on when called.
- Duration strings follow the pattern `"{number}{unit}"` where unit is `Y` for years.

