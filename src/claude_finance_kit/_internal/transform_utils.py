"""DataFrame column utilities and HTML-to-text helpers."""

from typing import Any, Optional

import pandas as pd
from bs4 import BeautifulSoup


def clean_numeric_string(value: Any) -> Any:
    """Strip grouping separators (comma, NBSP) and normalise decimal point."""
    if not isinstance(value, str):
        return value
    return value.replace("\u00a0", "").replace(",", "").strip()


def reorder_cols(
    df: pd.DataFrame,
    cols: str | list[str],
    position: str = "first",
) -> pd.DataFrame:
    """Move one or more columns to the start or end of a DataFrame."""
    if isinstance(cols, str):
        cols = [cols]
    move = [c for c in cols if c in df.columns]
    if not move:
        return df
    others = [c for c in df.columns if c not in move]
    order = move + others if position.lower() == "first" else others + move
    return df[order]


def flatten_hierarchical_index(
    df: pd.DataFrame,
    separator: str = "_",
    text_replacements: Optional[dict[str, str]] = None,
) -> pd.DataFrame:
    """Flatten a MultiIndex column structure to a single string-level."""
    result = df.copy()
    if not isinstance(result.columns, pd.MultiIndex):
        return result

    flat = result.columns.to_flat_index()

    def _join(col_tuple: tuple) -> str:
        parts = [str(lvl) for lvl in col_tuple if lvl != ""]
        name = separator.join(parts)
        if text_replacements:
            for old, new in text_replacements.items():
                name = name.replace(old, new)
        return name

    result.columns = [_join(c) for c in flat]
    return result


def clean_html_dict(
    data: dict[str, Any],
    html_keys: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Convert HTML strings in dict values to readable plain text."""
    if not isinstance(data, dict):
        return data
    result = data.copy()
    if html_keys is None:
        html_keys = [k for k, v in data.items() if isinstance(v, str) and "<" in v and ">" in v]
    for key in html_keys:
        if key in result and isinstance(result[key], str):
            try:
                soup = BeautifulSoup(result[key], "html.parser")
                for br in soup.find_all("br"):
                    br.replace_with("\n")
                for li in soup.find_all("li"):
                    li.insert_before("- ")
                text = " ".join(soup.get_text().split()).replace("- ", "\n- ")
                result[key] = text
            except Exception:
                pass
    return result
