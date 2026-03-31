"""Abstract base class and default data transformers for the pipeline."""

import abc
import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class Transformer(abc.ABC):
    """Abstract transformer that defines the transform interface."""

    @abc.abstractmethod
    def transform(self, data: Any) -> Any:
        """Transform raw data into a cleaned/normalised form.

        Args:
            data: Raw data to transform.

        Returns:
            Transformed data.
        """
        raise NotImplementedError


class BaseDataFrameTransformer(Transformer):
    """Normalises a DataFrame: parses time/date column, sorts, resets index.

    Operates on a copy so the caller's original data is not mutated.
    """

    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        for col in ("time", "date"):
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
                df = df.sort_values(col).reset_index(drop=True)
                break
        logger.debug("Transformed DataFrame: %d rows", len(df))
        return df


class DeduplicatingTransformer(BaseDataFrameTransformer):
    """Extends BaseDataFrameTransformer with duplicate-row removal.

    Attributes:
        dedup_subset: Column names used to identify duplicate rows.
                      Defaults to ["time"] if not overridden.
    """

    dedup_subset: list[str] = ["time"]

    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        df = super().transform(data)
        subset = [col for col in self.dedup_subset if col in df.columns]
        if subset:
            before = len(df)
            df = df.drop_duplicates(subset=subset).reset_index(drop=True)
            dropped = before - len(df)
            if dropped:
                logger.debug("Removed %d duplicate rows on %s", dropped, subset)
        return df


class PassThroughTransformer(Transformer):
    """No-op transformer — returns data unchanged.

    Useful for financial statement dicts that are exported as-is.
    """

    def transform(self, data: Any) -> Any:
        return data
