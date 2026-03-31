"""Custom exception hierarchy for claude-finance-kit."""

from typing import Any


class ClaudeFinanceKitError(Exception):
    """Base exception for all claude-finance-kit errors."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.error_code = error_code or "CLAUDE_FINANCE_KIT_000"
        self.details = details or {}
        super().__init__(self._format())

    def _format(self) -> str:
        msg = f"[{self.error_code}] {self.message}"
        if self.details:
            parts = ", ".join(f"{k}={v}" for k, v in self.details.items())
            msg += f" ({parts})"
        return msg

    def __str__(self) -> str:
        return self._format()

    def to_dict(self) -> dict[str, Any]:
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "type": self.__class__.__name__,
        }


class ProviderError(ClaudeFinanceKitError):
    """Raised for provider-related failures."""

    def __init__(
        self,
        message: str,
        provider: str | None = None,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        details = details or {}
        if provider:
            details["provider"] = provider
        super().__init__(message, error_code or "PROVIDER_000", details)


class InvalidSymbolError(ClaudeFinanceKitError):
    """Raised when an invalid or unrecognised symbol is provided."""

    def __init__(self, symbol: str, details: dict[str, Any] | None = None):
        details = details or {}
        details["symbol"] = symbol
        super().__init__(f"Invalid symbol: '{symbol}'", "SYMBOL_001", details)


class DataNotFoundError(ClaudeFinanceKitError):
    """Raised when requested data cannot be found."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        details = details or {}
        if symbol:
            details["symbol"] = symbol
        super().__init__(message, "DATA_404", details)


class RateLimitError(ClaudeFinanceKitError):
    """Raised when an API rate limit is exceeded."""

    def __init__(
        self,
        provider: str,
        retry_after: int | None = None,
        details: dict[str, Any] | None = None,
    ):
        details = details or {}
        details["provider"] = provider
        if retry_after is not None:
            details["retry_after"] = retry_after
        msg = f"Rate limit exceeded for provider '{provider}'"
        if retry_after is not None:
            msg += f". Retry after {retry_after}s"
        super().__init__(msg, "NETWORK_429", details)


class SourceNotAvailableError(ClaudeFinanceKitError):
    """Raised when a data source is not registered or unavailable."""

    def __init__(
        self,
        source: str,
        available: list[str] | None = None,
        details: dict[str, Any] | None = None,
    ):
        details = details or {}
        details["source"] = source
        if available is not None:
            details["available_sources"] = available
        super().__init__(f"Source '{source}' is not available", "SOURCE_001", details)


class InvalidDateRangeError(ClaudeFinanceKitError):
    """Raised when the supplied date range is invalid."""

    def __init__(
        self,
        start: str,
        end: str,
        details: dict[str, Any] | None = None,
    ):
        details = details or {}
        details["start"] = start
        details["end"] = end
        super().__init__(
            f"Invalid date range: start='{start}' end='{end}'",
            "DATE_001",
            details,
        )
