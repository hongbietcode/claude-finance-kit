"""MacroProvider implementation using MaybankTrade (MBK) API."""

import logging
from datetime import datetime

import pandas as pd

from claude_finance_kit._internal.http_client import send_request
from claude_finance_kit._provider._base import MacroProvider
from claude_finance_kit._provider._registry import registry

logger = logging.getLogger(__name__)

_BASE_URL = "https://data.maybanktrade.com.vn/"
_MACRO_DATA_PATH = "data/reportdatatopbynormtype"
_DATE_FMT = "%Y-%m-%d"

_REPORT_PERIOD = {
    "day": "1",
    "month": "2",
    "quarter": "3",
    "year": "4",
}

_TYPE_ID = {
    "gdp": "43",
    "cpi": "52",
    "industrial_production": "46",
    "export_import": "48",
    "retail": "47",
    "fdi": "50",
    "money_supply": "51",
    "exchange_rate": "53",
    "population_labor": "55",
    "interest_rate": "66",
}

_HEADERS = {
    "accept": "application/json",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "user-agent": "claude-finance-kit/1.0",
}


def _camel_to_snake(name: str) -> str:
    import re
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _resolve_end(end: str | None) -> str:
    if end is None:
        return datetime.now().strftime(_DATE_FMT)
    s = str(end)
    if len(s) == 4 and s.isdigit():
        return f"{s}-12-31"
    if len(s) == 7 and "-" in s:
        y, m = map(int, s.split("-"))
        return pd.Period(f"{y}-{m}", freq="M").end_time.strftime(_DATE_FMT)
    return s


def _resolve_start(start: str | None, end_date: str, length: str = "1Y") -> str:
    if start is not None:
        s = str(start)
        if len(s) == 4 and s.isdigit():
            return f"{s}-01-01"
        if len(s) == 7 and "-" in s:
            return f"{s}-01"
        return s
    from datetime import timedelta
    end_dt = datetime.strptime(end_date, _DATE_FMT)
    length = length.upper()
    if length.endswith("Y"):
        return end_dt.replace(year=end_dt.year - int(length[:-1])).strftime(_DATE_FMT)
    if length.endswith("M"):
        months = int(length[:-1])
        total = end_dt.month - months
        year = end_dt.year + total // 12
        month = total % 12
        if month <= 0:
            year -= 1
            month += 12
        return end_dt.replace(year=year, month=month).strftime(_DATE_FMT)
    if length.endswith("D"):
        return (end_dt - timedelta(days=int(length[:-1]))).strftime(_DATE_FMT)
    return end_dt.replace(year=end_dt.year - 1).strftime(_DATE_FMT)


def _build_period_params(start_date: str, end_date: str, period: str, indicator: str) -> tuple[str, str, str, str]:
    """Return (from_year, to_year, from_period, to_period) for the POST payload."""
    s_parts = start_date.split("-")
    e_parts = end_date.split("-")
    from_year, to_year = s_parts[0], e_parts[0]

    if indicator in ("exchange_rate", "interest_rate") and period == "day":
        return from_year, to_year, start_date, end_date

    if period == "year":
        return from_year, to_year, "0", "0"

    if period == "quarter":
        from_q = str((int(s_parts[1]) - 1) // 3)
        to_q = str((int(e_parts[1]) - 1) // 3)
        return from_year, to_year, from_q, to_q

    if period == "month":
        return from_year, to_year, str(int(s_parts[1])), str(int(e_parts[1]))

    return from_year, to_year, "0", "0"


def _fetch_macro(indicator: str, start: str | None, end: str | None, period: str) -> pd.DataFrame:
    if period not in _REPORT_PERIOD:
        raise ValueError(f"Unsupported period: '{period}'. Use: {list(_REPORT_PERIOD)}")
    type_id = _TYPE_ID.get(indicator)
    if type_id is None:
        raise ValueError(f"Unknown indicator: '{indicator}'")

    end_date = _resolve_end(end)
    start_date = _resolve_start(start, end_date)
    from_year, to_year, from_p, to_p = _build_period_params(start_date, end_date, period, indicator)

    period_code = _REPORT_PERIOD[period]
    payload = f"type={period_code}&fromYear={from_year}&toYear={to_year}&from={from_p}&to={to_p}&normTypeID={type_id}"

    try:
        raw = send_request(
            url=f"{_BASE_URL}{_MACRO_DATA_PATH}",
            headers=_HEADERS,
            method="POST",
            payload=payload,
        )
        df: pd.DataFrame = pd.DataFrame(raw)
        df.columns = [_camel_to_snake(c) for c in df.columns]
        for suffix in ("tern_", "norm_", "term_", "from_", "_code"):
            df.columns = df.columns.str.replace(suffix, "", regex=False)
        drop_cols = ["report_data_id", "id", "day", "group_id", "css_style", "type_id"]
        df: pd.DataFrame = df.drop(columns=[c for c in drop_cols if c in df.columns])

        if "day" in df.columns:
            ts = pd.to_numeric(
                df["day"].str.replace(  # pylint: disable=unsubscriptable-object
                    "/Date(", "", regex=False
                ).str.replace(")/", "", regex=False),
                errors="coerce",
            )
            df["last_updated"] = pd.to_datetime(ts, unit="ms").dt.date  # pylint: disable=unsupported-assignment-operation

        return df
    except Exception as exc:
        logger.error("_fetch_macro(%s) failed: %s", indicator, exc)
        raise


class MBKProvider(MacroProvider):
    """Macroeconomic data provider backed by MaybankTrade API."""

    def gdp(self, start: str | None = None, end: str | None = None, period: str = "quarter") -> pd.DataFrame:
        """GDP data. period: 'quarter' or 'year'."""
        if period not in ("quarter", "year"):
            raise ValueError(f"gdp() period must be 'quarter' or 'year', got '{period}'")
        return _fetch_macro("gdp", start, end, period)

    def cpi(self, length: str = "2Y", period: str = "month") -> pd.DataFrame:
        """CPI data. period: 'month' or 'year'."""
        if period not in ("month", "year"):
            raise ValueError(f"cpi() period must be 'month' or 'year', got '{period}'")
        end_date = _resolve_end(None)
        start_date = _resolve_start(None, end_date, length)
        df = _fetch_macro("cpi", start_date, end_date, period)
        if "group_name" in df.columns:
            df = df.drop(columns=["group_name"])
        return df

    def interest_rate(self, start: str | None = None, end: str | None = None) -> pd.DataFrame:
        """Interest rate data (daily), returned as pivot table."""
        df = _fetch_macro("interest_rate", start, end, "day")
        required = {"report_time", "group_name", "name", "value"}
        if required.issubset(df.columns):
            df["report_time"] = pd.to_datetime(df["report_time"], dayfirst=True, errors="coerce")
            try:
                pivot = df.pivot_table(index="report_time", columns=["group_name", "name"], values="value")
                return pivot.sort_index(axis=1, level=[0, 1])
            except Exception:
                pass
        return df

    def exchange_rate(self, start: str | None = None, end: str | None = None) -> pd.DataFrame:
        """Exchange rate data (daily)."""
        df = _fetch_macro("exchange_rate", start, end, "day")
        if "group_name" in df.columns:
            df = df.drop(columns=["group_name"])
        if "report_time" in df.columns:
            df["report_time"] = pd.to_datetime(df["report_time"], dayfirst=True, errors="coerce")
        return df

    def fdi(self, start: str | None = None, end: str | None = None, period: str = "month") -> pd.DataFrame:
        """Foreign Direct Investment data. period: 'month' or 'year'."""
        if period not in ("month", "year"):
            raise ValueError(f"fdi() period must be 'month' or 'year', got '{period}'")
        return _fetch_macro("fdi", start, end, period)

    def trade_balance(self, start: str | None = None, end: str | None = None, period: str = "month") -> pd.DataFrame:
        """Import/export trade balance data. period: 'month' or 'year'."""
        if period not in ("month", "year"):
            raise ValueError(f"trade_balance() period must be 'month' or 'year', got '{period}'")
        df = _fetch_macro("export_import", start, end, period)
        if "group_name" in df.columns:
            df = df.drop(columns=["group_name"])
        return df


registry.register_macro("MBK", MBKProvider)
