"""Task scheduler with concurrency control, rate limiting, and retry logic."""

import asyncio
import csv
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

try:
    from tqdm import tqdm
except ImportError:  # tqdm is optional
    def tqdm(iterable, **kwargs):  # type: ignore[misc]
        return iterable

from claude_finance_kit.collector.core.exporter import Exporter
from claude_finance_kit.collector.core.fetcher import Fetcher
from claude_finance_kit.collector.core.transformer import Transformer
from claude_finance_kit.collector.core.validator import Validator

logger = logging.getLogger(__name__)

_PARALLEL_THRESHOLD = 10


def _in_jupyter() -> bool:
    try:
        shell = get_ipython().__class__.__name__  # type: ignore[name-defined]
        return shell == "ZMQInteractiveShell"
    except NameError:
        return False


class Scheduler:
    """Orchestrates fetch → validate → transform → export for a list of tickers.

    For lists longer than _PARALLEL_THRESHOLD, processing runs in parallel via
    asyncio + ThreadPoolExecutor.  Shorter lists are processed sequentially.
    Progress is reported via tqdm when available.

    Args:
        fetcher: Fetcher instance.
        validator: Validator instance.
        transformer: Transformer instance.
        exporter: Optional Exporter instance.
        retry_attempts: Max retry count per ticker (default 3).
        backoff_factor: Exponential backoff multiplier (default 2.0).
        max_workers: Thread pool size for parallel mode (default 3).
        request_delay: Seconds to sleep between requests (default 0.5).
        rate_limit_wait: Seconds to wait after a rate-limit error (default 35.0).
    """

    def __init__(
        self,
        fetcher: Fetcher,
        validator: Validator,
        transformer: Transformer,
        exporter: Exporter | None = None,
        retry_attempts: int = 3,
        backoff_factor: float = 2.0,
        max_workers: int = 3,
        request_delay: float = 0.5,
        rate_limit_wait: float = 35.0,
    ) -> None:
        self.fetcher = fetcher
        self.validator = validator
        self.transformer = transformer
        self.exporter = exporter
        self.retry_attempts = retry_attempts
        self.backoff_factor = backoff_factor
        self.max_workers = max_workers
        self.request_delay = request_delay
        self.rate_limit_wait = rate_limit_wait

    def process_ticker(
        self,
        ticker: str,
        fetcher_kwargs: dict[str, Any] | None = None,
        exporter_kwargs: dict[str, Any] | None = None,
    ) -> None:
        """Process a single ticker: fetch → validate → transform → export with retry.

        Args:
            ticker: Stock symbol to process.
            fetcher_kwargs: Extra kwargs forwarded to fetcher.fetch().
            exporter_kwargs: Extra kwargs forwarded to exporter.export().

        Raises:
            Exception: Re-raises the last exception after all retries are exhausted.
        """
        attempt = 0
        success = False
        while attempt < self.retry_attempts and not success:
            attempt += 1
            try:
                time.sleep(self.request_delay)
                data = self.fetcher.fetch(ticker, **(fetcher_kwargs or {}))
                if not self.validator.validate(data):
                    raise ValueError(f"Validation failed for {ticker}.")
                transformed = self.transformer.transform(data)
                if self.exporter:
                    self.exporter.export(transformed, ticker, **(exporter_kwargs or {}))
                success = True
                logger.info("[%s] Processed successfully on attempt %d.", ticker, attempt)
            except Exception as exc:
                msg = str(exc).lower()
                if "rate limit" in msg or "too many" in msg:
                    logger.warning(
                        "[%s] Rate limited. Waiting %.0fs before retry…",
                        ticker,
                        self.rate_limit_wait,
                    )
                    time.sleep(self.rate_limit_wait)
                else:
                    logger.warning("[%s] Attempt %d failed: %s", ticker, attempt, exc)
                    if attempt < self.retry_attempts:
                        time.sleep(self.backoff_factor ** attempt)
                    else:
                        raise

    async def _run_async(
        self,
        tickers: list[str],
        fetcher_kwargs: dict[str, Any] | None = None,
        exporter_kwargs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run ticker processing in parallel using asyncio + ThreadPoolExecutor."""
        success_count = 0
        fail_count = 0
        errors: list[tuple[str, str]] = []
        started = time.time()

        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=self.max_workers)
        futures = {
            loop.run_in_executor(
                executor,
                lambda t=ticker: self.process_ticker(
                    t,
                    fetcher_kwargs=fetcher_kwargs,
                    exporter_kwargs=exporter_kwargs,
                ),
            ): ticker
            for ticker in tickers
        }

        progress = tqdm(total=len(futures), desc="Processing tickers")
        for future in asyncio.as_completed(list(futures)):
            ticker_name = futures[future]
            try:
                await future
                success_count += 1
            except Exception as exc:
                fail_count += 1
                errors.append((ticker_name, str(exc)))
                logger.error("Ticker %s failed: %s", ticker_name, exc)
            progress.update(1)  # type: ignore[union-attr]
        progress.close()  # type: ignore[union-attr]

        elapsed = time.time() - started
        avg = elapsed / len(tickers) if tickers else 0.0
        return {
            "success": success_count,
            "fail": fail_count,
            "total_time": elapsed,
            "avg_speed": avg,
            "errors": errors,
        }

    def run(
        self,
        tickers: list[str],
        fetcher_kwargs: dict[str, Any] | None = None,
        exporter_kwargs: dict[str, Any] | None = None,
        max_workers: int | None = None,
        request_delay: float | None = None,
        rate_limit_wait: float | None = None,
    ) -> dict[str, Any]:
        """Run the pipeline for all tickers and return a summary dict.

        Uses parallel processing when len(tickers) > _PARALLEL_THRESHOLD.

        Args:
            tickers: List of stock symbols.
            fetcher_kwargs: Extra kwargs forwarded to each fetcher.fetch() call.
            exporter_kwargs: Extra kwargs forwarded to each exporter.export() call.
            max_workers: Override instance max_workers for this run.
            request_delay: Override instance request_delay for this run.
            rate_limit_wait: Override instance rate_limit_wait for this run.

        Returns:
            Summary dict with keys: success, fail, total_time, avg_speed, errors.
        """
        if max_workers is not None:
            self.max_workers = max_workers
        if request_delay is not None:
            self.request_delay = request_delay
        if rate_limit_wait is not None:
            self.rate_limit_wait = rate_limit_wait

        started = time.time()
        total = len(tickers)
        result: dict[str, Any]

        if total > _PARALLEL_THRESHOLD:
            logger.info("Using parallel processing for %d tickers.", total)
            if _in_jupyter():
                try:
                    import nest_asyncio
                    nest_asyncio.apply()
                    loop = asyncio.get_event_loop()
                    result = loop.run_until_complete(
                        self._run_async(tickers, fetcher_kwargs, exporter_kwargs)
                    )
                except ImportError:
                    logger.warning("nest_asyncio not installed; falling back to asyncio.run()")
                    result = asyncio.run(self._run_async(tickers, fetcher_kwargs, exporter_kwargs))
            else:
                try:
                    loop = asyncio.get_running_loop()
                    result = loop.run_until_complete(
                        self._run_async(tickers, fetcher_kwargs, exporter_kwargs)
                    )
                except RuntimeError:
                    result = asyncio.run(self._run_async(tickers, fetcher_kwargs, exporter_kwargs))
        else:
            logger.info("Processing %d tickers sequentially.", total)
            success_count = 0
            fail_count = 0
            errors: list[tuple[str, str]] = []
            for ticker in tqdm(tickers, desc="Processing tickers"):
                try:
                    self.process_ticker(ticker, fetcher_kwargs=fetcher_kwargs, exporter_kwargs=exporter_kwargs)
                    success_count += 1
                except Exception as exc:
                    fail_count += 1
                    errors.append((ticker, str(exc)))
                    logger.error("Ticker %s failed: %s", ticker, exc)
            elapsed = time.time() - started
            result = {
                "success": success_count,
                "fail": fail_count,
                "total_time": elapsed,
                "avg_speed": elapsed / total if total else 0.0,
                "errors": errors,
            }

        print(
            f"Scheduler run complete. "
            f"Success: {result['success']}, Fail: {result['fail']}, "
            f"Total time: {result['total_time']:.2f}s, "
            f"Avg per ticker: {result['avg_speed']:.2f}s"
        )

        if result["errors"]:
            log_path = "error_log.csv"
            with open(log_path, "w", newline="", encoding="utf-8") as fh:
                writer = csv.writer(fh)
                writer.writerow(["Ticker", "Error"])
                writer.writerows(result["errors"])
            print(f"Error log saved to {log_path}.")

        return result
