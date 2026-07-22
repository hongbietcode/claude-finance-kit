"""Stock Screener — multi-criteria screening for Vietnamese stocks.

Usage: python scripts/stock-screener.py [--group VN30] [--strategy magic|canslim|multifactor] [--top 10]
Output: JSON with ranked stocks and scores

Strategies:
  magic     — Greenblatt Magic Formula (ROC + Earnings Yield)
  canslim   — CAN SLIM adaptation (7-point score)
  multifactor — Value + Quality + Momentum composite z-scores
"""

import argparse
import json
from datetime import datetime, timedelta

RATIO_COLUMNS = {
    "pe": ("pe", "pe_ratio"),
    "pb": ("pb", "pb_ratio"),
    "roe": ("roe",),
    "roic": ("roic", "return_on_capital_employed_roce"),
    "eps": ("eps", "trailing_eps", "earnings_per_share"),
}


def main():
    parser = argparse.ArgumentParser(description="Stock screener")
    parser.add_argument("--group", default="VN30", help="Stock group: VN30, VNMidCap, VNSmallCap, VNAllShare")
    parser.add_argument("--strategy", default="magic", choices=["magic", "canslim", "multifactor"])
    parser.add_argument("--top", type=int, default=10, help="Top N results")
    parser.add_argument("--source", default="VCI", help="Data source")
    args = parser.parse_args()

    from claude_finance_kit import Stock
    from claude_finance_kit.core.exceptions import ProviderError

    try:
        symbols = Stock("FPT", source=args.source).listing.symbols_by_group(args.group)
    except (ProviderError, Exception):
        symbols = Stock("FPT", source="KBS").listing.symbols_by_group(args.group)

    if hasattr(symbols, "tolist"):
        symbol_list = symbols["symbol"].tolist() if "symbol" in getattr(symbols, "columns", []) else symbols.tolist()
    else:
        symbol_list = list(symbols)

    if args.strategy == "magic":
        results = screen_magic_formula(symbol_list, args.source)
    elif args.strategy == "canslim":
        results = screen_canslim(symbol_list, args.source)
    else:
        results = screen_multifactor(symbol_list, args.source)

    results.sort(key=lambda x: x.get("rank_score", 0), reverse=True)

    output = {
        "strategy": args.strategy,
        "group": args.group,
        "total_screened": len(symbol_list),
        "results": results[: args.top],
        "timestamp": datetime.now().isoformat(),
    }

    print(json.dumps(output, ensure_ascii=False, default=str))


def get_ratios(stock):
    """Get normalized ratio rows in newest-first order."""
    ratios = stock.finance.ratio(period="quarter")
    if not ratios.empty:
        ratios = ratios.loc[:, ~ratios.columns.duplicated()]
        sort_columns = [column for column in ("year", "period") if column in ratios.columns]
        if sort_columns:
            ratios = ratios.sort_values(sort_columns, ascending=False, kind="stable").reset_index(drop=True)
    return ratios


def ratio_value(ratios, metric, row=0, default=0.0):
    """Read a normalized metric using verified provider aliases."""
    if ratios.empty or row >= len(ratios):
        return default
    for column in RATIO_COLUMNS[metric]:
        value = ratios.iloc[row].get(column)
        if column in ratios.columns and value is not None and value == value:
            return float(value)
    return default


def screen_magic_formula(symbols, source):
    results = []
    for sym in symbols:
        try:
            stock = safe_stock(sym, source)
            ratios = get_ratios(stock)
            if ratios.empty:
                continue
            pe = ratio_value(ratios, "pe")
            pb = ratio_value(ratios, "pb")
            roe = ratio_value(ratios, "roe")
            roic = ratio_value(ratios, "roic")
            if pe <= 0 or pb <= 0:
                continue
            ey = 1 / pe if pe > 0 else 0
            roc = roic if roic > 0 else roe
            results.append({
                "symbol": sym,
                "roc": round(roc, 4),
                "earnings_yield": round(ey, 4),
                "pe": round(pe, 2),
                "rank_score": round(roc + ey, 4),
            })
        except Exception:
            continue
    return results


def screen_canslim(symbols, source):
    results = []
    for sym in symbols:
        try:
            stock = safe_stock(sym, source)
            ratios = get_ratios(stock)
            if ratios.empty:
                continue
            score = 0

            eps_current = ratio_value(ratios, "eps", row=0, default=float("nan"))
            eps_prev = ratio_value(ratios, "eps", row=1, default=float("nan"))
            if eps_current == eps_current and eps_prev == eps_prev:
                if eps_prev > 0 and (eps_current - eps_prev) / eps_prev > 0.25:
                    score += 1

            annual_ratios = stock.finance.ratio(period="year")
            if not annual_ratios.empty:
                annual_ratios = annual_ratios.loc[:, ~annual_ratios.columns.duplicated()]
                annual_ratios = annual_ratios.sort_values("year", ascending=False, kind="stable")
                eps_y0 = ratio_value(annual_ratios, "eps", row=0, default=float("nan"))
                eps_y1 = ratio_value(annual_ratios, "eps", row=1, default=float("nan"))
                if eps_y0 == eps_y0 and eps_y1 == eps_y1:
                    if eps_y1 > 0 and (eps_y0 - eps_y1) / eps_y1 > 0.25:
                        score += 1

            history = stock.quote.history(
                start=(datetime.now() - timedelta(days=252)).strftime("%Y-%m-%d")
            )
            if not history.empty:
                high_52w = float(history["close"].max())
                current = float(history["close"].iloc[-1])
                if current >= high_52w * 0.95:
                    score += 1

            results.append({"symbol": sym, "canslim_score": score, "rank_score": score})
        except Exception:
            continue
    return results


def screen_multifactor(symbols, source):
    import statistics

    data = []
    for sym in symbols:
        try:
            stock = safe_stock(sym, source)
            ratios = get_ratios(stock)
            history = stock.quote.history(
                start=(datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
            )
            if ratios.empty or history.empty:
                continue
            pe = ratio_value(ratios, "pe")
            pb = ratio_value(ratios, "pb")
            roe = ratio_value(ratios, "roe")
            momentum = float(history["close"].iloc[-1]) / float(history["close"].iloc[0]) - 1
            if pe > 0 and pb > 0:
                data.append({"symbol": sym, "pe": pe, "pb": pb, "roe": roe, "momentum": momentum})
        except Exception:
            continue

    if len(data) < 3:
        return data

    for metric in ["pe", "pb", "roe", "momentum"]:
        values = [d[metric] for d in data]
        mean = statistics.mean(values)
        stdev = statistics.stdev(values) if len(values) > 1 else 1
        for d in data:
            z = (d[metric] - mean) / stdev if stdev > 0 else 0
            if metric in ["pe", "pb"]:
                z = -z
            d[f"z_{metric}"] = round(z, 3)

    for d in data:
        d["rank_score"] = round(
            sum(d.get(f"z_{m}", 0) for m in ["pe", "pb", "roe", "momentum"]) / 4, 3
        )

    return data


def safe_stock(symbol, source):
    from claude_finance_kit import Stock
    from claude_finance_kit.core.exceptions import ProviderError
    try:
        return Stock(symbol, source=source)
    except (ProviderError, Exception):
        return Stock(symbol, source="KBS")


if __name__ == "__main__":
    main()
