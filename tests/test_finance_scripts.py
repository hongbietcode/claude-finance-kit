"""Compatibility tests for shipped finance-kit data scripts."""

import importlib.util
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parents[1]
SCRIPT_DIR = ROOT / "cli" / "assets" / "skills" / "finance-kit" / "scripts"


def _load_script(name: str):
    path = SCRIPT_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_single_metric_reads_latest_normalized_ratio_alias():
    script = _load_script("fetch-single-metric")
    ratios = pd.DataFrame(
        [
            {"year": 2025, "period": "Q4", "pe": 12.0},
            {"year": 2026, "period": "Q1", "pe": 10.5},
        ]
    )

    assert script.latest_ratio_value(ratios, script.STOCK_METRICS["pe"]) == 10.5


def test_stock_screener_sorts_ratio_rows_and_reads_snake_case_metrics():
    script = _load_script("stock-screener")
    frame = pd.DataFrame(
        [
            {"year": 2025, "period": "Q4", "pe": 12.0, "roe": 0.18},
            {"year": 2026, "period": "Q1", "pe": 10.5, "roe": 0.21},
        ]
    )
    stock = type("Stock", (), {"finance": type("Finance", (), {"ratio": lambda self, period: frame})()})()

    ratios = script.get_ratios(stock)

    assert ratios.loc[0, "year"] == 2026
    assert script.ratio_value(ratios, "pe") == 10.5
    assert script.ratio_value(ratios, "roe") == 0.21
