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
    "pe": ("ratio", "priceToEarning"),
    "pb": ("ratio", "priceToBook"),
    "roe": ("ratio", "roe"),
    "roa": ("ratio", "roa"),
    "eps": ("ratio", "earningPerShare"),
    "dividend_yield": ("ratio", "dividend"),
    "debt_equity": ("ratio", "debtOnEquity"),
    "current_ratio": ("ratio", "currentPayment"),
    "gross_margin": ("ratio", "grossProfitMargin"),
    "net_margin": ("ratio", "postTaxMargin"),
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
        result = fetch_overview_field(args.ticker, args.source, "marketCap")
    elif metric in STOCK_METRICS:
        result = fetch_ratio_metric(args.ticker, args.source, metric)
    else:
        result = {"error": f"Unknown metric: {metric}. Available: {', '.join(list(STOCK_METRICS.keys()) + ['price', 'market_cap'] + list(MARKET_METRICS))}"}

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
    _, col = STOCK_METRICS[metric]
    val = ratios.iloc[0].get(col)
    return {"ticker": ticker, "metric": metric, "value": float(val) if val is not None else None}


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


def fetch_overview_field(ticker, source, field):
    from claude_finance_kit import Stock
    from claude_finance_kit.core.exceptions import ProviderError
    try:
        stock = Stock(ticker, source=source)
        overview = stock.company.overview()
    except (ProviderError, Exception):
        stock = Stock(ticker, source="KBS")
        overview = stock.company.overview()
    if overview.empty:
        return {"ticker": ticker, "metric": field, "value": None}
    val = overview.iloc[0].get(field)
    return {"ticker": ticker, "metric": field, "value": float(val) if val is not None else None}


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
