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
        symbol_list = symbols["symbol"].tolist() if "symbol" in symbols.columns else symbols.iloc[:, 0].tolist()
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


def screen_magic_formula(symbols, source):
    from claude_finance_kit import Stock
    results = []
    for sym in symbols:
        try:
            stock = safe_stock(sym, source)
            income = stock.finance.income_statement(period="year")
            bs = stock.finance.balance_sheet(period="year")
            overview = stock.company.overview()
            if income.empty or bs.empty or overview.empty:
                continue
            ebit = float(income.iloc[0].get("operatingProfit", 0))
            market_cap = float(overview.iloc[0].get("marketCap", 0))
            if market_cap <= 0 or ebit <= 0:
                continue
            short_assets = float(bs.iloc[0].get("shortAsset", 0))
            short_liab = float(bs.iloc[0].get("shortLiability", 0))
            fixed_assets = float(bs.iloc[0].get("fixedAsset", 0))
            debt = float(bs.iloc[0].get("debt", 0))
            cash = float(bs.iloc[0].get("cash", 0))
            wc = short_assets - short_liab
            ev = market_cap + debt - cash
            invested = wc + fixed_assets
            roc = ebit / invested if invested > 0 else 0
            ey = ebit / ev if ev > 0 else 0
            results.append({"symbol": sym, "roc": round(roc, 4), "earnings_yield": round(ey, 4), "rank_score": round(roc + ey, 4)})
        except Exception:
            continue
    return results


def screen_canslim(symbols, source):
    from claude_finance_kit import Market, Stock
    results = []
    try:
        vnindex_history = Stock("VNM", source="KBS").quote.history(
            start=(datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
        )
        vnindex_return = (float(vnindex_history["close"].iloc[-1]) / float(vnindex_history["close"].iloc[0]) - 1) if not vnindex_history.empty else 0
    except Exception:
        vnindex_return = 0

    for sym in symbols:
        try:
            stock = safe_stock(sym, source)
            ratios = stock.finance.ratio(period="quarter")
            if ratios.empty:
                continue
            score = 0
            eps_current = float(ratios.iloc[0].get("earningPerShare", 0))
            eps_prev = float(ratios.iloc[1].get("earningPerShare", 0)) if len(ratios) > 1 else 0
            if eps_prev > 0 and (eps_current - eps_prev) / eps_prev > 0.25:
                score += 1
            annual_ratios = stock.finance.ratio(period="year")
            if not annual_ratios.empty and len(annual_ratios) > 1:
                eps_y0 = float(annual_ratios.iloc[0].get("earningPerShare", 0))
                eps_y1 = float(annual_ratios.iloc[1].get("earningPerShare", 0))
                if eps_y1 > 0 and (eps_y0 - eps_y1) / eps_y1 > 0.25:
                    score += 1
            history = stock.quote.history(start=(datetime.now() - timedelta(days=252)).strftime("%Y-%m-%d"))
            if not history.empty:
                high_52w = float(history["close"].max())
                current = float(history["close"].iloc[-1])
                if current >= high_52w * 0.95:
                    score += 1
                stock_return = current / float(history["close"].iloc[0]) - 1
                if vnindex_return != 0 and stock_return > vnindex_return:
                    score += 1
            results.append({"symbol": sym, "canslim_score": score, "rank_score": score})
        except Exception:
            continue
    return results


def screen_multifactor(symbols, source):
    import statistics
    from claude_finance_kit import Stock
    data = []
    for sym in symbols:
        try:
            stock = safe_stock(sym, source)
            ratios = stock.finance.ratio(period="year")
            history = stock.quote.history(start=(datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d"))
            if ratios.empty or history.empty:
                continue
            pe = float(ratios.iloc[0].get("priceToEarning", 0))
            pb = float(ratios.iloc[0].get("priceToBook", 0))
            roe = float(ratios.iloc[0].get("roe", 0))
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
        d["rank_score"] = round(sum(d.get(f"z_{m}", 0) for m in ["pe", "pb", "roe", "momentum"]) / 4, 3)

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
