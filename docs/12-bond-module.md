# Bond Module

The `Bond` facade exposes Vietnamese corporate and government bond discovery plus
market data through the same registered providers used by `Stock`.

## Quick Start

```python
from claude_finance_kit import Bond

bonds = Bond(source="VCI").list()
corporate = Bond(source="VCI").list("corporate")

bond = Bond("BAB123032", source="VCI")
history = bond.ohlcv(start="2025-01-01", end="2025-12-31", interval="1D")
trades = bond.trades()
current = bond.quote()
```

## Symbol Types

Bond validation is intentionally narrow:

| Input | Asset type | Instrument type |
|-------|------------|-----------------|
| Corporate bond such as `BAB123032` | `bond` | `BOND` |
| Government bond such as `GB10F2024` | `bond` | `FUND_BOND` |

`get_asset_type()` treats both corporate and government bond codes as bonds so
the facade can route them through the same bond provider path. `get_instrument_type()`
adds the finer distinction between corporate bonds, government bonds, ETFs, and
listed funds.

## API

| Method | Returns | Description |
|--------|---------|-------------|
| `list(bond_type="all")` | `DataFrame` | Lists `corporate`, `government`, or all supported bonds |
| `ohlcv(symbol=None, start=None, end=None, interval="1D")` | `DataFrame` | Historical OHLCV bars; `start` is required |
| `trades(symbol=None)` | `DataFrame` | Recent matched trades |
| `quote(symbol=None)` | `DataFrame` | Current price-board row |

Pass a symbol to the constructor or to an individual data method. `start`
must use `YYYY-MM-DD`.

`Bond.list()` returns a `symbol`/`type` DataFrame and stores metadata in
`df.attrs["source"]` plus `df.attrs["unsupported_types"]` when the provider cannot
serve a requested class.

## Providers

VCI is the default and supports both corporate and government bond discovery
plus OHLCV, matched trades, and current quote data.

KBS can be selected with `source="KBS"`, but it does not provide government-bond
discovery. `Bond(source="KBS").list("government")` raises `NotImplementedError`;
`Bond(source="KBS").list()` still returns corporate results and records
`["government"]` in `df.attrs["unsupported_types"]`.

An upstream symbol with no trades returns an empty `DataFrame` rather than
fabricated data.
