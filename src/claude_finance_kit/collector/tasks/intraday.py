"""Intraday data batch fetch task using claude_finance_kit.stock.Stock."""

import logging
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from claude_finance_kit.collector.core.exporter import Exporter
from claude_finance_kit.collector.core.fetcher import StockFetcher
from claude_finance_kit.collector.core.scheduler import Scheduler
from claude_finance_kit.collector.core.transformer import DeduplicatingTransformer
from claude_finance_kit.collector.core.validator import DataFrameValidator

logger = logging.getLogger(__name__)


class IntradayFetcher(StockFetcher):
    """Fetches intraday tick data for a ticker via Stock.quote.intraday()."""

    def _call(self, ticker: str, **kwargs: Any) -> pd.DataFrame:
        from claude_finance_kit.stock import Stock

        stock = Stock(ticker)
        return stock.quote.intraday()


class IntradayValidator(DataFrameValidator):
    """Validates that intraday DataFrame contains required tick columns."""

    required_columns = ["time", "price", "volume"]


class IntradayTransformer(DeduplicatingTransformer):
    """Normalises and deduplicates intraday data on (time, id) when available."""

    dedup_subset = ["time", "id"]

    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        df = super().transform(data)
        if "time" in df.columns:
            df["time"] = pd.to_datetime(df["time"], errors="coerce")
            df = df.sort_values("time").reset_index(drop=True)
        return df


class SmartCSVExporter(Exporter):
    """Appends intraday data to per-ticker CSV files with smart deduplication.

    Uses an atomic write (write to .tmp then rename) to avoid corrupt files on
    interruption.  Keeps at most max_backups timestamped backups per ticker.
    """

    def __init__(
        self,
        base_path: str,
        backup_dir: str | None = None,
        max_backups: int = 2,
    ) -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.backup_dir = Path(backup_dir) if backup_dir else self.base_path / "backup"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.max_backups = max_backups

    def _file_path(self, ticker: str) -> Path:
        return self.base_path / f"{ticker}.csv"

    def _cleanup_old_backups(self, ticker: str) -> None:
        backups = sorted(
            self.backup_dir.glob(f"{ticker}_*.csv"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for old in backups[self.max_backups:]:
            try:
                old.unlink()
            except Exception as exc:
                logger.warning("Could not remove old backup %s: %s", old.name, exc)

    def _backup(self, ticker: str) -> bool:
        src = self._file_path(ticker)
        if not src.exists():
            return False
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = self.backup_dir / f"{ticker}_{stamp}.csv"
        shutil.copy2(src, dst)
        self._cleanup_old_backups(ticker)
        return True

    def _atomic_write(self, df: pd.DataFrame, path: Path) -> None:
        tmp = path.with_suffix(".csv.tmp")
        df.to_csv(tmp, index=False)
        os.replace(tmp, path)

    def _read_existing(self, ticker: str) -> pd.DataFrame:
        path = self._file_path(ticker)
        if not path.exists():
            return pd.DataFrame()
        try:
            df = pd.read_csv(path)
            if "time" in df.columns:
                df["time"] = pd.to_datetime(df["time"], errors="coerce")
            return df
        except Exception as exc:
            logger.warning("Could not read existing data for %s: %s", ticker, exc)
            return pd.DataFrame()

    def _smart_merge(self, old: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
        if old.empty:
            return new
        if new.empty:
            return old
        for df in (old, new):
            if "time" not in df.columns:
                raise ValueError("DataFrame must have a 'time' column")
            df["time"] = pd.to_datetime(df["time"], errors="coerce")
        old = old.sort_values("time")
        new = new.sort_values("time")
        cutoff = new["time"].min().replace(second=0, microsecond=0)
        base = old[old["time"] < cutoff]
        merged = pd.concat([base, new])
        dedup_cols = ["time", "id"] if "id" in merged.columns else ["time"]
        merged = merged.drop_duplicates(subset=dedup_cols).reset_index(drop=True)
        return merged.sort_values("time").reset_index(drop=True)

    def export(
        self,
        data: pd.DataFrame,
        ticker: str,
        mode: str = "append",
        backup: bool = True,
        **kwargs: Any,
    ) -> None:
        if data is None or data.empty:
            return
        if "time" in data.columns:
            data = data.copy()
            data["time"] = pd.to_datetime(data["time"], errors="coerce")
        path = self._file_path(ticker)
        if mode == "append" and path.exists():
            if backup:
                self._backup(ticker)
            existing = self._read_existing(ticker)
            merged = self._smart_merge(existing, data)
            self._atomic_write(merged, path)
        else:
            self._atomic_write(data, path)

    def preview(self, ticker: str, n: int = 5, **kwargs: Any) -> pd.DataFrame | None:
        path = self._file_path(ticker)
        if not path.exists():
            return None
        try:
            df = pd.read_csv(path)
            if "time" in df.columns:
                df["time"] = pd.to_datetime(df["time"], errors="coerce")
                df = df.sort_values("time", ascending=False)
            return df.head(n)
        except Exception as exc:
            logger.warning("SmartCSVExporter preview failed for %s: %s", ticker, exc)
            return None


class IntradayTask:
    """High-level intraday batch task supporting EOD (one-shot) and live modes.

    Usage (EOD):
        task = IntradayTask()
        task.run(["ACB", "VCB"], mode="eod")

    Usage (live — loops until KeyboardInterrupt):
        task = IntradayTask()
        task.run(["ACB", "VCB"], mode="live", interval=60)
    """

    def __init__(
        self,
        base_path: str = "./data/intraday",
        max_backups: int = 2,
        max_workers: int = 3,
        request_delay: float = 0.5,
        rate_limit_wait: float = 35.0,
    ) -> None:
        self._fetcher = IntradayFetcher()
        self._validator = IntradayValidator()
        self._transformer = IntradayTransformer()
        self._base_path = base_path
        self._max_backups = max_backups
        self._max_workers = max_workers
        self._request_delay = request_delay
        self._rate_limit_wait = rate_limit_wait

    def _make_scheduler(self, exporter: Exporter) -> Scheduler:
        return Scheduler(
            fetcher=self._fetcher,
            validator=self._validator,
            transformer=self._transformer,
            exporter=exporter,
            retry_attempts=3,
            max_workers=self._max_workers,
            request_delay=self._request_delay,
            rate_limit_wait=self._rate_limit_wait,
        )

    def run(
        self,
        tickers: list[str],
        mode: str = "live",
        interval: int = 60,
        backup: bool = True,
    ) -> None:
        """Run intraday data collection.

        Args:
            tickers: Stock symbols to process.
            mode: "eod" for one-shot, "live" for continuous loop.
            interval: Seconds between live updates.
            backup: Whether to create backup files before each live update.
        """
        from claude_finance_kit.collector.core.exporter import CSVExporter

        if mode.lower() == "eod":
            logger.info("EOD mode: fetching intraday data once.")
            exporter: Exporter = CSVExporter(base_path=self._base_path)
            scheduler = self._make_scheduler(exporter)
            scheduler.run(tickers)
            return

        logger.info("Live mode: continuous intraday updates every %ds.", interval)
        smart_exporter = SmartCSVExporter(
            base_path=self._base_path,
            max_backups=self._max_backups,
        )
        scheduler = self._make_scheduler(smart_exporter)
        export_kwargs = {"mode": "append", "backup": backup}
        try:
            while True:
                scheduler.run(tickers, exporter_kwargs=export_kwargs)
                logger.info("Update complete. Sleeping %ds.", interval)
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("Live intraday loop stopped by user.")


def run_intraday_task(
    tickers: list[str],
    mode: str = "live",
    interval: int = 60,
    backup: bool = True,
    max_backups: int = 2,
) -> None:
    """Convenience function to run the intraday task.

    Args:
        tickers: Stock symbols to process.
        mode: "eod" or "live".
        interval: Seconds between live updates.
        backup: Whether to backup before each live update.
        max_backups: Maximum backup files retained per ticker.
    """
    task = IntradayTask(max_backups=max_backups)
    task.run(tickers, mode=mode, interval=interval, backup=backup)
