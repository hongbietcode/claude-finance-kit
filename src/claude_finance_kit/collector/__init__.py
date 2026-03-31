"""claude_finance_kit collector: batch data fetching, scheduling, and exporting."""

from claude_finance_kit.collector.core.exporter import (
    CSVExporter,
    DuckDBExporter,
    Exporter,
    ParquetExporter,
    TimeSeriesExporter,
)
from claude_finance_kit.collector.core.fetcher import Fetcher, StockFetcher
from claude_finance_kit.collector.core.scheduler import Scheduler
from claude_finance_kit.collector.core.transformer import (
    BaseDataFrameTransformer,
    DeduplicatingTransformer,
    PassThroughTransformer,
    Transformer,
)
from claude_finance_kit.collector.core.validator import (
    DataFrameValidator,
    DictOfDataFramesValidator,
    Validator,
)
from claude_finance_kit.collector.tasks.financial import FinancialTask, run_financial_task
from claude_finance_kit.collector.tasks.intraday import IntradayTask, run_intraday_task
from claude_finance_kit.collector.tasks.ohlcv import OHLCVTask
from claude_finance_kit.collector.tasks.ohlcv import run_task as run_ohlcv_task

__all__ = [
    "Scheduler",
    "Fetcher",
    "StockFetcher",
    "Validator",
    "DataFrameValidator",
    "DictOfDataFramesValidator",
    "Transformer",
    "BaseDataFrameTransformer",
    "DeduplicatingTransformer",
    "PassThroughTransformer",
    "Exporter",
    "CSVExporter",
    "ParquetExporter",
    "DuckDBExporter",
    "TimeSeriesExporter",
    "OHLCVTask",
    "run_ohlcv_task",
    "FinancialTask",
    "run_financial_task",
    "IntradayTask",
    "run_intraday_task",
]
