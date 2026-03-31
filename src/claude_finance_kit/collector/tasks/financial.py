"""Financial statements batch fetch task using claude_finance_kit.stock.Stock."""

import logging
import os
from pathlib import Path
from typing import Any

import pandas as pd

from claude_finance_kit.collector.core.exporter import Exporter
from claude_finance_kit.collector.core.fetcher import StockFetcher
from claude_finance_kit.collector.core.scheduler import Scheduler
from claude_finance_kit.collector.core.transformer import PassThroughTransformer
from claude_finance_kit.collector.core.validator import DictOfDataFramesValidator

logger = logging.getLogger(__name__)

_REPORT_KEYS = (
    "balance_sheet",
    "income_statement_year",
    "income_statement_quarter",
    "cash_flow",
    "ratio",
)


class FinancialFetcher(StockFetcher):
    """Fetches all financial statements for a ticker via Stock.finance.*().

    Returns a dict keyed by report name.  Each value is a DataFrame or None
    if the request fails.

    Accepted kwargs:
        balance_sheet_period (str): "year" or "quarter".
        income_statement_year_period (str): "year" or "quarter".
        income_statement_quarter_period (str): "year" or "quarter".
        cash_flow_period (str): "year" or "quarter".
        ratio_period (str): "year" or "quarter".
    """

    def _call(self, ticker: str, **kwargs: Any) -> dict[str, pd.DataFrame | None]:
        from claude_finance_kit.stock import Stock

        stock = Stock(ticker)
        finance = stock.finance

        bs_period = kwargs.get("balance_sheet_period", "year")
        is_year_period = kwargs.get("income_statement_year_period", "year")
        is_qtr_period = kwargs.get("income_statement_quarter_period", "quarter")
        cf_period = kwargs.get("cash_flow_period", "year")
        ratio_period = kwargs.get("ratio_period", "year")

        result: dict[str, pd.DataFrame | None] = {}

        for key, method, period in (
            ("balance_sheet", finance.balance_sheet, bs_period),
            ("income_statement_year", finance.income_statement, is_year_period),
            ("income_statement_quarter", finance.income_statement, is_qtr_period),
            ("cash_flow", finance.cash_flow, cf_period),
            ("ratio", finance.ratio, ratio_period),
        ):
            try:
                result[key] = method(period=period)
            except Exception as exc:
                logger.warning("Failed to fetch %s for %s: %s", key, ticker, exc)
                result[key] = None

        return result


class FinancialExporter(Exporter):
    """Exports each financial statement DataFrame to a separate CSV file.

    Files are written as: base_path/{ticker}_{report_name}.csv
    """

    def __init__(self, base_path: str) -> None:
        self.base_path = base_path
        Path(base_path).mkdir(parents=True, exist_ok=True)

    def export(self, data: dict[str, pd.DataFrame | None], ticker: str, **kwargs: Any) -> None:
        for report_name, df in data.items():
            if df is None or df.empty:
                continue
            path = os.path.join(self.base_path, f"{ticker}_{report_name}.csv")
            df.to_csv(path, index=False)
            logger.info("Saved %s for %s to %s", report_name, ticker, path)


class FinancialTask:
    """High-level financial statements batch task.

    Usage:
        task = FinancialTask(base_path="./data/financial")
        task.run(["ACB", "VCB"], balance_sheet_period="year")
    """

    def __init__(
        self,
        base_path: str = "./data/financial",
        retry_attempts: int = 1,
        max_workers: int = 3,
        request_delay: float = 0.5,
        rate_limit_wait: float = 35.0,
    ) -> None:
        self._fetcher = FinancialFetcher()
        self._validator = DictOfDataFramesValidator()
        self._transformer = PassThroughTransformer()
        self._exporter = FinancialExporter(base_path=base_path)
        self._scheduler = Scheduler(
            fetcher=self._fetcher,
            validator=self._validator,
            transformer=self._transformer,
            exporter=self._exporter,
            retry_attempts=retry_attempts,
            max_workers=max_workers,
            request_delay=request_delay,
            rate_limit_wait=rate_limit_wait,
        )

    def run(self, tickers: list[str], **fetch_kwargs: Any) -> dict[str, Any]:
        """Run the financial pipeline for a list of tickers.

        Args:
            tickers: Stock symbols to process.
            **fetch_kwargs: Period overrides forwarded to FinancialFetcher.

        Returns:
            Scheduler summary dict.
        """
        return self._scheduler.run(tickers, fetcher_kwargs=fetch_kwargs or None)


def run_financial_task(
    tickers: list[str],
    max_workers: int = 3,
    request_delay: float = 0.5,
    rate_limit_wait: float = 35.0,
    **kwargs: Any,
) -> dict[str, Any]:
    """Convenience function to run the financial statements task.

    Args:
        tickers: Stock symbols to process.
        max_workers: Parallel worker count.
        request_delay: Seconds between requests.
        rate_limit_wait: Seconds to wait after a rate-limit error.
        **kwargs: Period overrides forwarded to FinancialFetcher.

    Returns:
        Scheduler summary dict.
    """
    task = FinancialTask(
        max_workers=max_workers,
        request_delay=request_delay,
        rate_limit_wait=rate_limit_wait,
    )
    return task.run(tickers, **kwargs)
