"""Fetch Single Metric — quick lookup for one data point.

Usage: python scripts/fetch-single-metric.py TICKER METRIC [--source VCI]

Metrics: pe, pb, roe, roa, eps, price, market_cap, dividend_yield,
         debt_equity, current_ratio, gross_margin, net_margin,
         vnindex_pe, cpi, interest_rate, exchange_rate

Output: JSON with metric name and value
"""

import argparse
import json
from datetime import datetime

STOCK_METRICS = {
    "pe": ("pe", "pe_ratio"),
    "pb": ("pb", "pb_ratio"),
    "roe": ("roe",),
    "roa": ("roa",),
    "eps": ("eps", "trailing_eps", "earnings_per_share"),
    "dividend_yield": ("dividend_yield",),
    "debt_equity": ("debt_to_equity",),
    "current_ratio": ("current_ratio", "short_term_ratio"),
    "gross_margin": ("gross_margin",),
    "net_margin": ("net_margin", "after_tax_profit_margin"),
}

MARKET_METRICS = {"vnindex_pe", "cpi", "interest_rate", "exchange_rate"}


def main():
    parser = argparse.ArgumentParser(description="Fetch single metric")
    parser.add_argument("ticker", help="Ticker or 'market' for macro metrics")
    parser.add_argument("metric", help="Metric name")
    parser.add_argument("--source", default="VCI")
    args = parser.parse_args()

    metric = args.metric.lower().replace("-", "_")

    if metric in MARKET_METRICS:
        result = fetch_market_metric(metric)
    elif metric == "price":
        result = fetch_price(args.ticker, args.source)
    elif metric == "market_cap":
        result = fetch_market_cap(args.ticker, args.source)
    elif metric in STOCK_METRICS:
        result = fetch_ratio_metric(args.ticker, args.source, metric)
    else:
        available = list(STOCK_METRICS) + ["price", "market_cap"] + list(MARKET_METRICS)
        result = {"error": f"Unknown metric: {metric}. Available: {', '.join(available)}"}

    result["timestamp"] = datetime.now().isoformat()
    print(json.dumps(result, ensure_ascii=False, default=str))


def fetch_ratio_metric(ticker, source, metric):
    from claude_finance_kit import Stock
    from claude_finance_kit.core.exceptions import ProviderError
    try:
        stock = Stock(ticker, source=source)
        ratios = stock.finance.ratio(period="quarter")
    except (ProviderError, Exception):
        stock = Stock(ticker, source="KBS")
        ratios = stock.finance.ratio(period="quarter")
    if ratios.empty:
        return {"ticker": ticker, "metric": metric, "value": None, "error": "no data"}
    val = latest_ratio_value(ratios, STOCK_METRICS[metric])
    return {"ticker": ticker, "metric": metric, "value": float(val) if val is not None else None}


def latest_ratio_value(ratios, columns):
    """Return the newest available normalized ratio metric."""
    if ratios.empty:
        return None
    ratios = ratios.loc[:, ~ratios.columns.duplicated()]
    sort_columns = [column for column in ("year", "period") if column in ratios.columns]
    if sort_columns:
        ratios = ratios.sort_values(sort_columns, ascending=False, kind="stable")
    row = ratios.iloc[0]
    for column in columns:
        value = row.get(column)
        if column in ratios.columns and value is not None and value == value:
            return value
    return None


def fetch_price(ticker, source):
    from claude_finance_kit import Stock
    from claude_finance_kit.core.exceptions import ProviderError
    try:
        stock = Stock(ticker, source=source)
        df = stock.quote.intraday()
    except (ProviderError, Exception):
        stock = Stock(ticker, source="KBS")
        df = stock.quote.intraday()
    if df.empty:
        return {"ticker": ticker, "metric": "price", "value": None}
    last = df.iloc[-1]
    return {"ticker": ticker, "metric": "price", "value": float(last.get("close", last.get("price", 0)))}


def fetch_market_cap(ticker, source):
    from claude_finance_kit import Stock
    from claude_finance_kit.core.exceptions import ProviderError
    try:
        stock = Stock(ticker, source=source)
        ratios = stock.finance.ratio(period="quarter")
    except (ProviderError, Exception):
        stock = Stock(ticker, source="KBS")
        ratios = stock.finance.ratio(period="quarter")
    val = latest_ratio_value(ratios, ("market_cap",))
    if val is None:
        return {"ticker": ticker, "metric": "market_cap", "value": None}
    return {"ticker": ticker, "metric": "market_cap", "value": float(val) if val is not None else None}


def fetch_market_metric(metric):
    if metric == "vnindex_pe":
        from claude_finance_kit import Market
        pe = Market("VNINDEX").pe(duration="1Y")
        if pe.empty:
            return {"metric": metric, "value": None}
        return {"metric": metric, "value": round(float(pe.iloc[-1]["pe"]), 2)}
    from claude_finance_kit import Macro
    macro = Macro()
    fn_map = {"cpi": macro.cpi, "interest_rate": macro.interest_rate, "exchange_rate": macro.exchange_rate}
    fn = fn_map.get(metric)
    if not fn:
        return {"metric": metric, "error": "unknown"}
    df = fn()
    if df.empty:
        return {"metric": metric, "value": None}
    return {"metric": metric, "latest": df.iloc[-1].to_dict()}


if __name__ == "__main__":
    main()
