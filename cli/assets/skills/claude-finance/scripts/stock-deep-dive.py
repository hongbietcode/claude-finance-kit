"""Stock Deep Dive — fetch fundamental + technical + news data for a single ticker.

Usage: python scripts/stock-deep-dive.py TICKER [--source KBS] [--days 200]
Output: JSON to stdout with sections: overview, financials, ratios, technicals, news
"""

import argparse
import json
import sys
from datetime import datetime, timedelta


def main():
    parser = argparse.ArgumentParser(description="Stock deep dive data collector")
    parser.add_argument("ticker", help="Stock ticker symbol (e.g. FPT)")
    parser.add_argument("--source", default="VCI", help="Data source: VCI or KBS")
    parser.add_argument("--days", type=int, default=200, help="History days for TA")
    args = parser.parse_args()

    from claude_finance_kit import Stock
    from claude_finance_kit.core.exceptions import ProviderError

    try:
        stock = Stock(args.ticker, source=args.source)
        stock.quote.history(start=(datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"))
    except (ProviderError, Exception):
        stock = Stock(args.ticker, source="KBS")

    result = {"ticker": args.ticker, "source": stock._source, "timestamp": datetime.now().isoformat()}
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d")

    try:
        overview = stock.company.overview()
        result["overview"] = overview.to_dict(orient="records") if not overview.empty else []
    except Exception as e:
        result["overview"] = {"error": str(e)}

    try:
        ratios = stock.finance.ratio(period="quarter")
        result["ratios"] = ratios.head(4).to_dict(orient="records") if not ratios.empty else []
    except Exception as e:
        result["ratios"] = {"error": str(e)}

    try:
        bs = stock.finance.balance_sheet(period="quarter")
        result["balance_sheet"] = bs.head(4).to_dict(orient="records") if not bs.empty else []
    except Exception as e:
        result["balance_sheet"] = {"error": str(e)}

    try:
        income = stock.finance.income_statement(period="quarter")
        result["income_statement"] = income.head(4).to_dict(orient="records") if not income.empty else []
    except Exception as e:
        result["income_statement"] = {"error": str(e)}

    try:
        cf = stock.finance.cash_flow(period="quarter")
        result["cash_flow"] = cf.head(4).to_dict(orient="records") if not cf.empty else []
    except Exception as e:
        result["cash_flow"] = {"error": str(e)}

    try:
        df = stock.quote.history(start=start, end=end)
        if not df.empty:
            from claude_finance_kit.ta import Indicator

            df_ta = df.set_index("time")
            ind = Indicator(df_ta)
            last = df_ta.iloc[-1]
            result["price"] = {
                "open": float(last["open"]),
                "high": float(last["high"]),
                "low": float(last["low"]),
                "close": float(last["close"]),
                "volume": int(last["volume"]),
            }
            result["technicals"] = {
                "sma_20": safe_last(ind.trend.sma(length=20)),
                "sma_50": safe_last(ind.trend.sma(length=50)),
                "sma_200": safe_last(ind.trend.sma(length=200)),
                "rsi_14": safe_last(ind.momentum.rsi(length=14)),
                "macd": safe_last_df(ind.momentum.macd()),
                "bbands": safe_last_df(ind.trend.bbands(length=20)),
                "atr_14": safe_last(ind.volatility.atr(length=14)),
            }
            result["ohlcv_last_30"] = json.loads(df.tail(30).to_json(orient="records", date_format="iso"))
        else:
            result["price"] = {"error": "empty"}
            result["technicals"] = {"error": "empty"}
    except Exception as e:
        result["price"] = {"error": str(e)}
        result["technicals"] = {"error": str(e)}

    try:
        news = stock.company.news(limit=10)
        result["news"] = news.to_dict(orient="records") if not news.empty else []
    except Exception as e:
        result["news"] = {"error": str(e)}

    try:
        events = stock.company.events()
        result["events"] = events.head(5).to_dict(orient="records") if not events.empty else []
    except Exception as e:
        result["events"] = {"error": str(e)}

    print(json.dumps(result, ensure_ascii=False, default=str))


def safe_last(series):
    try:
        val = series.dropna().iloc[-1]
        return round(float(val), 4)
    except Exception:
        return None


def safe_last_df(df):
    try:
        row = df.dropna().iloc[-1]
        return {k: round(float(v), 4) for k, v in row.items()}
    except Exception:
        return None


if __name__ == "__main__":
    main()
