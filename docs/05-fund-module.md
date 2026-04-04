# Fund Module

The `Fund` class provides data on Vietnamese open-ended investment funds, including fund listings, holdings, NAV history, and asset allocation.

## Quick Start

```python
from claude_finance_kit import Fund

fund = Fund()
fund = Fund(source="FMARKET")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source` | str | `"FMARKET"` | Data source identifier |

## Methods

All methods return a `pd.DataFrame`.

### listing(fund_type)

List available funds, optionally filtered by type.

```python
all_funds = fund.listing(fund_type="")
stock_funds = fund.listing(fund_type="STOCK")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `fund_type` | str | `"STOCK"` | Filter: `""` (all), `"BALANCED"`, `"BOND"`, `"STOCK"` |

### fund_filter(symbol)

Search for a fund by its short name or symbol.

```python
results = fund.fund_filter("VESAF")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `symbol` | str | required | Fund short name or partial match string |

### top_holding(fund_id)

Top stock holdings of a specific fund.

```python
holdings = fund.top_holding(fund_id="VESAF")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `fund_id` | str | required | Fund identifier from `listing()` or `fund_filter()` |

### industry_holding(fund_id)

Industry allocation breakdown for a fund.

```python
industries = fund.industry_holding(fund_id="VESAF")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `fund_id` | str | required | Fund identifier |

### nav_report(fund_id)

Full NAV (Net Asset Value) history for a fund.

```python
nav = fund.nav_report(fund_id="VESAF")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `fund_id` | str | required | Fund identifier |

### asset_holding(fund_id)

Asset allocation breakdown (stocks, bonds, cash, etc.).

```python
assets = fund.asset_holding(fund_id="VESAF")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `fund_id` | str | required | Fund identifier |

## Data Models

### `fund.listing()` → DataFrame

| Field | Type | Description |
|-------|------|-------------|
| `short_name` | str | Fund short name (e.g., "VFMVN30") |
| `name` | str | Full fund name |
| `fund_type` | str | Fund asset type (STOCK, BOND, BALANCED) |
| `fund_owner_name` | str | Fund management company name |
| `management_fee` | float | Annual management fee (%) |
| `inception_date` | str | Fund launch date (YYYY-MM-DD) |
| `nav` | float | Current NAV per unit |
| `nav_change_36m` | float | NAV change over 36 months (%) |
| `nav_change_36m_annualized` | float | Annualized 36-month return (%) |
| `nav_update_at` | str | NAV last updated (YYYY-MM-DD) |
| `fund_id_fmarket` | int | Fmarket internal fund ID (use for other calls) |
| `fund_code` | str | Fund code |

### `fund.fund_filter()` → DataFrame

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Fmarket fund ID |
| `shortName` | str | Fund short name |

### `fund.top_holding()` → DataFrame

| Field | Type | Description |
|-------|------|-------------|
| `stock_code` | str | Stock ticker or bond code |
| `industry` | str | Industry classification |
| `net_asset_percent` | float | Percentage of fund net assets (%) |
| `type_asset` | str | Asset type (equity, bond) |
| `update_at` | str | Last update date (YYYY-MM-DD) |
| `fundId` | int | Fund ID |

### `fund.industry_holding()` → DataFrame

| Field | Type | Description |
|-------|------|-------------|
| `industry` | str | Industry name |
| `net_asset_percent` | float | Percentage of fund allocated to this industry (%) |

### `fund.nav_report()` → DataFrame

| Field | Type | Description |
|-------|------|-------------|
| `date` | str | NAV date |
| `nav_per_unit` | float | NAV per unit on that date |

### `fund.asset_holding()` → DataFrame

| Field | Type | Description |
|-------|------|-------------|
| `asset_type` | str | Asset type (e.g., "Equity", "Bond", "Cash") |
| `asset_percent` | float | Percentage of total assets (%) |

## Examples

### Find a Fund and Inspect Holdings

A typical workflow: search for a fund, get its ID, then drill into its portfolio.

```python
from claude_finance_kit import Fund

fund = Fund()

results = fund.fund_filter("VESAF")
print(results[["fund_id", "name", "fund_type"]])

fund_id = results.iloc[0]["fund_id"]

holdings = fund.top_holding(fund_id)
print("\n=== Top Holdings ===")
print(holdings[["symbol", "weight"]].to_string(index=False))

industries = fund.industry_holding(fund_id)
print("\n=== Industry Allocation ===")
print(industries.to_string(index=False))
```

### Compare NAV Performance Across Funds

```python
fund = Fund()

fund_ids = ["VESAF", "VEOF", "VIBF"]
for fid in fund_ids:
    nav = fund.nav_report(fid)
    start_nav = nav.iloc[0]["nav"]
    end_nav = nav.iloc[-1]["nav"]
    return_pct = (end_nav - start_nav) / start_nav * 100
    print(f"{fid}: {return_pct:+.2f}% total return")
```

## Notes

- The `fund_id` value comes from `listing()` or `fund_filter()` results. Always query these first.
- Fund types: `"STOCK"` for equity funds, `"BOND"` for fixed-income, `"BALANCED"` for mixed.
- Pass an empty string `""` to `fund_type` in `listing()` to retrieve all fund types.
- NAV data frequency depends on the fund; most report daily NAV.

