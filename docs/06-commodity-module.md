# Commodity Module

The `Commodity` class provides Vietnamese and global commodity price data, covering gold, oil, steel, gas, fertilizer, and agricultural products.

## Quick Start

```python
from claude_finance_kit import Commodity

commodity = Commodity()
commodity = Commodity(source="SPL")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source` | str | `"SPL"` | Data source identifier |

## Common Parameters

All commodity methods share the same parameter signature:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start` | str or None | `None` | Start date `"YYYY-MM-DD"`. None for auto range. |
| `end` | str or None | `None` | End date `"YYYY-MM-DD"`. None for latest. |
| `length` | str | `"1Y"` | Shorthand lookback: `"3M"`, `"6M"`, `"1Y"`, `"2Y"`, `"5Y"` |

When `start` and `end` are provided, they take precedence over `length`.

## Methods

All methods return a `pd.DataFrame`.

### gold(start, end, length)

Vietnamese domestic and global gold prices (SJC, world gold).

```python
gold = commodity.gold(length="1Y")
gold = commodity.gold(start="2024-01-01", end="2024-12-31")
```

### oil(start, end, length)

Crude oil (Brent, WTI) and Vietnam retail gas prices.

```python
oil = commodity.oil(length="6M")
```

### steel(start, end, length)

Steel and iron ore prices.

```python
steel = commodity.steel(length="1Y")
```

### gas(start, end, length)

Natural gas prices.

```python
gas = commodity.gas(length="1Y")
```

### fertilizer(start, end, length)

Urea and other fertilizer prices.

```python
fert = commodity.fertilizer(length="2Y")
```

### agricultural(start, end, length)

Agricultural commodity prices including soybean, corn, and sugar.

```python
agri = commodity.agricultural(length="1Y")
```

## Data Models

All commodity methods return DataFrames with a `time` datetime index and price columns. Prices are daily closing prices.

### `commodity.gold()` → DataFrame

| Field | Type | Description |
|-------|------|-------------|
| `time` | datetime (index) | Trading date |
| `buy` | float | Vietnam gold buy price (VND/tael) |
| `sell` | float | Vietnam gold sell price (VND/tael) |
| `global` | float | Global gold price (USD/oz, GC=F futures) |

### `commodity.oil()` → DataFrame

| Field | Type | Description |
|-------|------|-------------|
| `time` | datetime (index) | Trading date |
| `crude_oil` | float | WTI crude oil price (USD/barrel, CL=F futures) |
| `ron95` | float | Vietnam RON95 gasoline price (VND/liter) |
| `ron92` | float | Vietnam RON92 gasoline price (VND/liter) |
| `oil_do` | float | Vietnam diesel (DO) price (VND/liter) |

### `commodity.steel()` → DataFrame

| Field | Type | Description |
|-------|------|-------------|
| `time` | datetime (index) | Trading date |
| `steel_d10` | float | Vietnam D10 rebar steel price (VND/kg) |
| `hrc` | float | Hot-rolled coil price (COMEX HRC futures) |
| `iron_ore` | float | Iron ore price (COMEX TIO futures) |

### `commodity.gas()` → DataFrame

| Field | Type | Description |
|-------|------|-------------|
| `time` | datetime (index) | Trading date |
| `natural_gas` | float | Natural gas price (USD/MMBtu, NG=F futures) |
| `crude_oil` | float | WTI crude oil price (USD/barrel) |

### `commodity.fertilizer()` → DataFrame

| Field | Type | Description |
|-------|------|-------------|
| `time` | datetime (index) | Trading date |
| `urea` | float | Urea fertilizer price (CBOT UME futures) |

### `commodity.agricultural()` → DataFrame

| Field | Type | Description |
|-------|------|-------------|
| `time` | datetime (index) | Trading date |
| `soybean` | float | Soybean meal price (USD, ZM=F futures) |
| `corn` | float | Corn price (USD, ZC=F futures) |
| `sugar` | float | Raw sugar price (USD, SB=F futures) |

## Examples

### Gold Price Trend

```python
from claude_finance_kit import Commodity

commodity = Commodity()
gold = commodity.gold(length="1Y")

print(f"Latest gold price: {gold.iloc[-1]['price']}")
print(f"52-week high: {gold['price'].max()}")
print(f"52-week low:  {gold['price'].min()}")
```

### Compare Oil and Gas Prices

```python
commodity = Commodity()

oil = commodity.oil(start="2024-01-01", end="2024-12-31")
gas = commodity.gas(start="2024-01-01", end="2024-12-31")

print("=== Oil (last 5 records) ===")
print(oil.tail(5).to_string(index=False))

print("\n=== Gas (last 5 records) ===")
print(gas.tail(5).to_string(index=False))
```

### Multi-Commodity Dashboard

```python
commodity = Commodity()

datasets = {
    "Gold": commodity.gold(length="3M"),
    "Oil": commodity.oil(length="3M"),
    "Steel": commodity.steel(length="3M"),
}

for name, df in datasets.items():
    latest = df.iloc[-1]["price"]
    first = df.iloc[0]["price"]
    change = (latest - first) / first * 100
    print(f"{name}: {latest:.2f} ({change:+.1f}% over 3M)")
```

## Notes

- Date parameters use `"YYYY-MM-DD"` format. Length shorthand: `"{number}{unit}"` (`M` months, `Y` years).
- Explicit `start`/`end` take precedence over `length`.
- Data availability varies by commodity; some may have gaps on non-trading days.

