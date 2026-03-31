"""
DataFrame transformation utilities — public facade.

Re-exports from split modules:
- transform_ohlcv: OHLCV normalisation, intraday conversion, resampling
- transform_utils: column helpers, HTML-to-text
"""

from claude_finance_kit._internal.transform_ohlcv import (
    get_trading_date,
    intraday_to_df,
    ohlc_to_df,
    resample_ohlcv,
)
from claude_finance_kit._internal.transform_utils import (
    clean_html_dict,
    clean_numeric_string,
    flatten_hierarchical_index,
    reorder_cols,
)

__all__ = [
    "get_trading_date",
    "intraday_to_df",
    "ohlc_to_df",
    "resample_ohlcv",
    "clean_html_dict",
    "clean_numeric_string",
    "flatten_hierarchical_index",
    "reorder_cols",
]
