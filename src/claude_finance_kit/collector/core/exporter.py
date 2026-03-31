"""Exporters for pipeline output: CSV, Parquet, DuckDB, and time-series layouts."""

import abc
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

_DATE_FMT = "%Y-%m-%d"


class Exporter(abc.ABC):
    """Abstract exporter that defines the export interface."""

    @abc.abstractmethod
    def export(self, data: Any, ticker: str, **kwargs: Any) -> Any:
        """Export processed data.

        Args:
            data: Transformed data (DataFrame or dict of DataFrames).
            ticker: Stock symbol.
            **kwargs: Additional export parameters.

        Returns:
            Output path or None depending on implementation.
        """
        raise NotImplementedError

    def preview(self, ticker: str, n: int = 5, **kwargs: Any) -> pd.DataFrame | None:
        """Return the last n rows of stored data for ticker, or None."""
        return None


class CSVExporter(Exporter):
    """Exports DataFrames to per-ticker CSV files under base_path.

    Appends to existing files and deduplicates on (time, id) when both
    columns are present.
    """

    def __init__(self, base_path: str) -> None:
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    def _file_path(self, ticker: str) -> str:
        return os.path.join(self.base_path, f"{ticker}.csv")

    def export(self, data: pd.DataFrame, ticker: str, **kwargs: Any) -> str:
        path = self._file_path(ticker)
        if os.path.exists(path):
            try:
                existing = pd.read_csv(path)
                merged = pd.concat([existing, data], ignore_index=True)
                if "time" in merged.columns and "id" in merged.columns:
                    merged = merged.drop_duplicates(subset=["time", "id"])
                merged.to_csv(path, index=False)
            except Exception as exc:
                logger.warning("CSVExporter merge failed for %s: %s — appending raw", ticker, exc)
                data.to_csv(path, mode="a", header=False, index=False)
        else:
            data.to_csv(path, index=False)
        return path

    def preview(self, ticker: str, n: int = 5, **kwargs: Any) -> pd.DataFrame | None:
        path = self._file_path(ticker)
        if not os.path.exists(path):
            return None
        try:
            return pd.read_csv(path).tail(n)
        except Exception as exc:
            logger.warning("CSVExporter preview failed for %s: %s", ticker, exc)
            return None


class ParquetExporter(Exporter):
    """Exports DataFrames to Parquet files organised as base_path/data_type/date/ticker.parquet.

    Requires pyarrow (optional dependency — ImportError raised at export time if missing).
    """

    def __init__(self, base_path: str, data_type: str = "stock_data") -> None:
        self.base_path = Path(base_path)
        self.data_type = data_type
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _file_path(self, ticker: str, date: str | None = None) -> Path:
        date_str = date or datetime.now().strftime(_DATE_FMT)
        folder = self.base_path / self.data_type / date_str
        folder.mkdir(parents=True, exist_ok=True)
        return folder / f"{ticker}.parquet"

    def export(self, data: pd.DataFrame, ticker: str, date: str | None = None, **kwargs: Any) -> Path:
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
        except ImportError as exc:
            raise ImportError("pyarrow is required for ParquetExporter: pip install pyarrow") from exc

        path = self._file_path(ticker, date)
        table = pa.Table.from_pandas(data)
        pq.write_table(table, path, compression="snappy", use_dictionary=True, version="2.6")
        return path

    def preview(self, ticker: str, n: int = 5, date: str | None = None, **kwargs: Any) -> pd.DataFrame | None:
        try:
            import pyarrow.parquet as pq
        except ImportError:
            return None
        path = self._file_path(ticker, date)
        if not path.exists():
            return None
        try:
            return pq.read_table(path).to_pandas().tail(n)
        except Exception as exc:
            logger.warning("ParquetExporter preview failed for %s: %s", ticker, exc)
            return None


class DuckDBExporter(Exporter):
    """Exports DataFrames to a DuckDB database file, one table per ticker.

    Requires duckdb (optional dependency — ImportError raised at export time if missing).
    """

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def export(self, data: pd.DataFrame, ticker: str, **kwargs: Any) -> None:
        try:
            import duckdb
        except ImportError as exc:
            raise ImportError("duckdb is required for DuckDBExporter: pip install duckdb") from exc

        con = duckdb.connect(self.db_path)
        try:
            con.execute(
                f"CREATE TABLE IF NOT EXISTS {ticker} AS SELECT * FROM data LIMIT 0",
                {"data": data},
            )
            con.execute(f"INSERT INTO {ticker} SELECT * FROM data", {"data": data})
        finally:
            con.close()


class TimeSeriesExporter(Exporter):
    """Flexible time-series exporter supporting CSV and Parquet formats.

    Directory layout: base_path/data_type/[subfolder]/YYYY-MM-DD/ticker.{csv|parquet}

    Supports append mode with optional deduplication on configurable columns.
    """

    def __init__(
        self,
        base_path: str,
        file_format: str = "csv",
        dedup_columns: list[str] | None = None,
    ) -> None:
        self.base_path = Path(base_path)
        self.file_format = file_format.lower()
        self.dedup_columns = dedup_columns or ["time", "ticker"]
        if self.file_format not in ("csv", "parquet"):
            raise ValueError("file_format must be 'csv' or 'parquet'")
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _build_path(
        self,
        ticker: str,
        data_type: str,
        date: str | None = None,
        subfolder: str | None = None,
    ) -> Path:
        date_str = date or datetime.now().strftime(_DATE_FMT)
        ext = "csv" if self.file_format == "csv" else "parquet"
        parts: list[Any] = [self.base_path, data_type]
        if subfolder:
            parts.append(subfolder)
        parts.append(date_str)
        folder = Path(*parts)
        folder.mkdir(parents=True, exist_ok=True)
        return folder / f"{ticker}.{ext}"

    def _read(self, path: Path) -> pd.DataFrame:
        if self.file_format == "csv":
            return pd.read_csv(path)
        return pd.read_parquet(path)

    def _write(self, path: Path, data: pd.DataFrame) -> None:
        if self.file_format == "csv":
            data.to_csv(path, index=False)
        else:
            data.to_parquet(path, engine="pyarrow", compression="snappy", index=False)

    def _deduplicate(self, data: pd.DataFrame) -> pd.DataFrame:
        subset = [col for col in self.dedup_columns if col in data.columns]
        if not subset:
            return data
        return data.drop_duplicates(subset=subset, keep="last").reset_index(drop=True)

    def export(
        self,
        data: pd.DataFrame,
        ticker: str,
        data_type: str = "intraday",
        date: str | None = None,
        append_mode: bool = True,
        deduplicate: bool = False,
        subfolder: str | None = None,
        **kwargs: Any,
    ) -> Path | None:
        if data is None or data.empty:
            return None
        path = self._build_path(ticker, data_type, date, subfolder)
        if path.exists() and append_mode:
            existing = self._read(path)
            merged = pd.concat([existing, data], ignore_index=True)
            if deduplicate:
                merged = self._deduplicate(merged)
            self._write(path, merged)
        else:
            out = self._deduplicate(data) if deduplicate else data
            self._write(path, out)
        return path

    def preview(
        self,
        ticker: str,
        n: int = 5,
        data_type: str = "intraday",
        date: str | None = None,
        subfolder: str | None = None,
        **kwargs: Any,
    ) -> pd.DataFrame | None:
        path = self._build_path(ticker, data_type, date, subfolder)
        if not path.exists():
            return None
        try:
            return self._read(path).tail(n)
        except Exception as exc:
            logger.warning("TimeSeriesExporter preview failed for %s: %s", ticker, exc)
            return None

    def read_all(
        self,
        ticker: str,
        data_type: str = "intraday",
        date: str | None = None,
        subfolder: str | None = None,
    ) -> pd.DataFrame | None:
        path = self._build_path(ticker, data_type, date, subfolder)
        if not path.exists():
            return None
        return self._read(path)

    def list_dates(
        self, ticker: str, data_type: str, subfolder: str | None = None
    ) -> list[str]:
        folder = self.base_path / data_type
        if subfolder:
            folder = folder / subfolder
        if not folder.exists():
            return []
        ext = "csv" if self.file_format == "csv" else "parquet"
        filename = f"{ticker}.{ext}"
        dates = [d.name for d in folder.iterdir() if d.is_dir() and (d / filename).exists()]
        return sorted(dates)

    def read_date_range(
        self,
        ticker: str,
        data_type: str,
        start_date: str,
        end_date: str,
        subfolder: str | None = None,
    ) -> pd.DataFrame:
        dates = [d for d in self.list_dates(ticker, data_type, subfolder) if start_date <= d <= end_date]
        frames = [self.read_all(ticker, data_type, d, subfolder) for d in dates]
        valid = [f for f in frames if f is not None]
        if not valid:
            return pd.DataFrame()
        return pd.concat(valid, ignore_index=True)
