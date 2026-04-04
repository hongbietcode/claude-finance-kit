# Macro Module

The `Macro` class provides Vietnamese macroeconomic indicators including GDP, CPI, interest rates, exchange rates, FDI, and trade balance data.

## Quick Start

```python
from claude_finance_kit import Macro

macro = Macro()
macro = Macro(source="MBK")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source` | str | `"MBK"` | Data source identifier |

## Methods

All methods return a `pd.DataFrame`.

### gdp(start, end, period)

Gross Domestic Product data for Vietnam.

```python
gdp = macro.gdp(start="2020-01-01", end="2024-12-31", period="quarter")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start` | str or None | `None` | Start date `"YYYY-MM-DD"`. None for earliest available. |
| `end` | str or None | `None` | End date `"YYYY-MM-DD"`. None for latest available. |
| `period` | str | `"quarter"` | Aggregation: `"quarter"` or `"year"` |

### cpi(length, period)

Consumer Price Index data.

```python
cpi = macro.cpi(length="2Y", period="month")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `length` | str | `"2Y"` | Lookback period: `"6M"`, `"1Y"`, `"2Y"`, `"5Y"` |
| `period` | str | `"month"` | Aggregation: `"month"` or `"year"` |

### interest_rate(start, end)

Daily interest rate pivot table across different tenors.

```python
rates = macro.interest_rate(start="2024-01-01", end="2024-12-31")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start` | str or None | `None` | Start date `"YYYY-MM-DD"` |
| `end` | str or None | `None` | End date `"YYYY-MM-DD"` |

### exchange_rate(start, end)

Daily exchange rate data (USD/VND and other currency pairs).

```python
fx = macro.exchange_rate(start="2024-01-01")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start` | str or None | `None` | Start date `"YYYY-MM-DD"` |
| `end` | str or None | `None` | End date `"YYYY-MM-DD"` |

### fdi(start, end, period)

Foreign Direct Investment inflows into Vietnam.

```python
fdi = macro.fdi(start="2022-01-01", period="month")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start` | str or None | `None` | Start date `"YYYY-MM-DD"` |
| `end` | str or None | `None` | End date `"YYYY-MM-DD"` |
| `period` | str | `"month"` | Aggregation: `"month"` or `"year"` |

### trade_balance(start, end, period)

Import/export trade balance data.

```python
trade = macro.trade_balance(start="2023-01-01", period="month")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start` | str or None | `None` | Start date `"YYYY-MM-DD"` |
| `end` | str or None | `None` | End date `"YYYY-MM-DD"` |
| `period` | str | `"month"` | Aggregation: `"month"` or `"year"` |

## Data Models

All macro methods return DataFrames from the MaybankTrade API. Columns are auto-translated from camelCase to snake_case.

### `macro.gdp()` → DataFrame

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | GDP component name (e.g., "GDP", "Agriculture", "Industry") |
| `value` | float | GDP value (unit depends on indicator) |
| `year` | str | Reporting year |
| `period` | str | Quarter number (1-4) or "0" for annual |

### `macro.cpi()` → DataFrame

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | CPI category (e.g., "General", "Food", "Transport") |
| `value` | float | CPI index value or percentage change |
| `year` | str | Reporting year |
| `period` | str | Month number (1-12) |

### `macro.interest_rate()` → DataFrame (Pivot Table)

Returns a pivot table with:
- **Index**: `report_time` (datetime) — daily date
- **Columns**: MultiIndex of (`group_name`, `name`) — e.g., ("Deposit", "1 month"), ("Lending", "Short term")
- **Values**: Interest rate percentages

### `macro.exchange_rate()` → DataFrame

| Field | Type | Description |
|-------|------|-------------|
| `report_time` | datetime | Date of the rate |
| `name` | str | Currency pair or rate type |
| `value` | float | Exchange rate value |

### `macro.fdi()` → DataFrame

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | FDI metric name (registered capital, disbursed capital, etc.) |
| `value` | float | FDI value (USD million) |
| `year` | str | Reporting year |
| `period` | str | Month or year period |

### `macro.trade_balance()` → DataFrame

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Trade metric (export, import, trade balance) |
| `value` | float | Value (USD million) |
| `year` | str | Reporting year |
| `period` | str | Month or year period |

## Examples

### GDP Growth Trend

```python
from claude_finance_kit import Macro

macro = Macro()
gdp = macro.gdp(start="2019-01-01", period="quarter")

print(gdp[["year", "name", "value"]].tail(12))
```

### CPI vs Interest Rate Comparison

```python
macro = Macro()

cpi = macro.cpi(length="2Y", period="month")
rates = macro.interest_rate(start="2024-01-01")

# interest_rate returns MultiIndex columns with report_time index
print("=== CPI (last 6 months) ===")
print(cpi.tail(6).to_string(index=False))

print("\n=== Interest Rate (last 6 entries) ===")
print(rates.tail(6))
```

## Notes

- All date parameters use `"YYYY-MM-DD"` format. `None` returns full available range.
- Period controls time aggregation; not all methods support both `"month"` and `"year"`.

