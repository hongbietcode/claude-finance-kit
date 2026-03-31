"""Abstract base class and default DataFrame validator for pipeline data quality checks."""

import abc
import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class Validator(abc.ABC):
    """Abstract validator that defines the validate interface."""

    @abc.abstractmethod
    def validate(self, data: Any) -> bool:
        """Validate data quality.

        Args:
            data: Data to validate.

        Returns:
            True if valid, False otherwise.
        """
        raise NotImplementedError


class DataFrameValidator(Validator):
    """Validates that data is a non-empty DataFrame containing required columns.

    Attributes:
        required_columns: List of column names that must be present.
    """

    required_columns: list[str] = []

    def validate(self, data: Any) -> bool:
        if not isinstance(data, pd.DataFrame):
            logger.error("Validation failed: data is not a DataFrame (got %s)", type(data).__name__)
            return False
        if data.empty:
            logger.warning("Validation failed: DataFrame is empty")
            return False
        missing = [col for col in self.required_columns if col not in data.columns]
        if missing:
            logger.warning("Validation failed: missing columns %s", missing)
            return False
        return True


class DictOfDataFramesValidator(Validator):
    """Validates a dict where at least one value is a non-empty DataFrame.

    Used for financial statement fetches that return multiple reports.
    """

    def validate(self, data: Any) -> bool:
        if not isinstance(data, dict):
            logger.error("Validation failed: expected dict, got %s", type(data).__name__)
            return False
        for key, value in data.items():
            if value is not None and isinstance(value, pd.DataFrame) and not value.empty:
                return True
        logger.warning("Validation failed: no valid DataFrames found in dict")
        return False
