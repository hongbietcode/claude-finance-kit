# Collector Module

Batch ETL for stock data: fetch, transform, validate, and export.

**Install:** `pip install claude-finance-kit[collector]`

## Quick Start

```python
from claude_finance_kit.collector import run_ohlcv_task, run_financial_task, run_intraday_task
```

## Pre-built Tasks

### OHLCV Task

Batch fetch historical OHLCV data for multiple symbols.

```python
from claude_finance_kit.collector import OHLCVTask, run_ohlcv_task

run_ohlcv_task(
    ["FPT", "VNM", "VIC"],
    start="2024-01-01",
    end="2024-12-31",
    interval="1D",
)

task = OHLCVTask(base_path="data/ohlcv")
task.run(["FPT", "VNM", "VIC"], start="2024-01-01", end="2024-12-31", interval="1D")
```

### Financial Task

Batch fetch financial statements (balance sheet, income, cash flow, ratios).

```python
from claude_finance_kit.collector import FinancialTask, run_financial_task

run_financial_task(["FPT", "VNM"], balance_sheet_period="quarter", ratio_period="quarter")

task = FinancialTask(base_path="data/financials")
task.run(
    ["FPT", "VNM"],
    balance_sheet_period="quarter",
    income_statement_quarter_period="quarter",
    cash_flow_period="quarter",
    ratio_period="quarter",
)
```

### Intraday Task

Batch fetch intraday tick data.

```python
from claude_finance_kit.collector import IntradayTask, run_intraday_task

run_intraday_task(["FPT", "VNM"], mode="eod")

task = IntradayTask(base_path="data/intraday")
task.run(["FPT", "VNM"], mode="live", interval=60, backup=True)
```

## Core Components

### Fetcher

`StockFetcher` is an abstract base. Custom fetchers subclass it and implement `_call()`.

```python
from typing import Any

from claude_finance_kit.collector import StockFetcher

class QuoteHistoryFetcher(StockFetcher):
    def _call(self, ticker: str, **kwargs: Any):
        from claude_finance_kit import Stock

        return Stock(ticker).quote.history(
            start=kwargs.get("start", "2024-01-01"),
            end=kwargs.get("end", "2024-12-31"),
            interval=kwargs.get("interval", "1D"),
        )


fetcher = QuoteHistoryFetcher()
df = fetcher.fetch("FPT", start="2024-01-01")
```

### Exporter

Save DataFrames to various formats.

```python
from claude_finance_kit.collector import CSVExporter, ParquetExporter, DuckDBExporter, TimeSeriesExporter

exporter = CSVExporter(base_path="data/")
exporter.export(df, ticker="FPT")

parquet = ParquetExporter(base_path="data/", data_type="ohlcv")
parquet.export(df, ticker="FPT")

duck = DuckDBExporter(db_path="data/stocks.duckdb")
duck.export(df, ticker="FPT")

ts = TimeSeriesExporter(base_path="data/", file_format="parquet")
ts.export(df, ticker="FPT", data_type="intraday", deduplicate=True)
```

### Transformer

Data transformation collector.

```python
from claude_finance_kit.collector import DeduplicatingTransformer, PassThroughTransformer

transformer = DeduplicatingTransformer()
clean_df = transformer.transform(df)

noop = PassThroughTransformer()
same_df = noop.transform(df)
```

### Validator

Data quality checks.

```python
from claude_finance_kit.collector import DataFrameValidator, DictOfDataFramesValidator

validator = DataFrameValidator()
validator.validate(df)

dict_validator = DictOfDataFramesValidator()
dict_validator.validate({"ohlcv": df1, "financials": df2})
```

### Scheduler

Orchestrate batch fetch collectors with retry and rate limiting.

```python
from claude_finance_kit.collector import CSVExporter, DataFrameValidator, DeduplicatingTransformer, Scheduler

validator = DataFrameValidator()
validator.required_columns = ["time", "open", "high", "low", "close", "volume"]
transformer = DeduplicatingTransformer()
exporter = CSVExporter(base_path="data/custom")

scheduler = Scheduler(
    fetcher=fetcher,
    validator=validator,
    transformer=transformer,
    exporter=exporter,
    retry_attempts=3, backoff_factor=2.0, max_workers=3,
    request_delay=0.5, rate_limit_wait=35.0,
)
scheduler.process_ticker("FPT", fetcher_kwargs={"start": "2024-01-01"})
scheduler.run(tickers=["FPT", "VNM"], fetcher_kwargs={"start": "2024-01-01"})
```

## WebSocket Streaming

Base client and utilities for real-time data streams.

```python
from claude_finance_kit.collector.stream import (
    BaseWebSocketClient, expand_data_type_group,
    get_data_type_description, validate_data_types,
)
```

## Data Models

### OHLCVTask Output

Each symbol produces a DataFrame with the standard OHLCV schema:

| Field | Type | Description |
|-------|------|-------------|
| `time` | datetime64 | Bar timestamp |
| `open` | float64 | Opening price |
| `high` | float64 | Highest price |
| `low` | float64 | Lowest price |
| `close` | float64 | Closing price |
| `volume` | int64 | Trading volume (shares) |

### FinancialTask Output

Produces a dict of DataFrames keyed by report type:

| Key | Description |
|-----|-------------|
| `balance_sheet` | Assets, liabilities, equity |
| `income_statement_year` | Annual revenue, expenses, net income |
| `income_statement_quarter` | Quarterly revenue, expenses, net income |
| `cash_flow` | Operating, investing, financing flows |
| `ratio` | Financial ratios (PE, PB, ROE, EPS, etc.) |

Each DataFrame has `symbol`, `year`, `period` index columns plus dynamic metric columns.

### IntradayTask Output

| Field | Type | Description |
|-------|------|-------------|
| `time` | datetime64 | Tick timestamp |
| `price` | float64 | Matched price |
| `volume` | int64 | Matched volume |
| `id` | int64 | Optional provider-specific trade identifier |

Additional provider-specific columns may be present depending on the intraday source.

### Exporter Formats

| Exporter | Format | Best For |
|----------|--------|----------|
| `CSVExporter` | CSV | Human-readable, Excel compatible |
| `ParquetExporter` | Parquet | Large datasets, columnar queries, preserves dtypes |
| `DuckDBExporter` | DuckDB | SQL queries, analytics |
| `TimeSeriesExporter` | Partitioned | Time-partitioned storage |

## Dependencies

Requires `[collector]` extra: duckdb, pyarrow, tqdm, aiohttp, nest-asyncio, websockets.

**See also:** [`references/common-patterns.md`](../references/common-patterns.md) — batch processing pattern, caching, error handling.
