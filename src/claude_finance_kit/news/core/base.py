"""Abstract base class for news parsers."""

import logging
from abc import ABC, abstractmethod


def setup_logger(name: str, debug: bool = False) -> logging.Logger:
    """Configure and return a named logger."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    if debug:
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(handler)
    else:
        logger.addHandler(logging.NullHandler())
        logger.propagate = False
    return logger


class BaseParser(ABC):
    """Abstract base defining a standard fetch → parse workflow."""

    def __init__(self, show_log: bool = False) -> None:
        self.logger = setup_logger(self.__class__.__name__, show_log)

    @abstractmethod
    def fetch(self):
        """Fetch raw data from the source (e.g. XML, HTML)."""

    @abstractmethod
    def parse(self, raw):
        """Parse raw data into structured form (e.g. DataFrame or dict)."""

    def run(self):
        """Execute fetch() followed by parse() and return the result."""
        raw = self.fetch()
        return self.parse(raw)
