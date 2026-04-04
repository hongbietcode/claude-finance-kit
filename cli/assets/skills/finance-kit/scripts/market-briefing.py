"""Market Briefing — fetch VNINDEX valuation, top movers, macro indicators, commodities.

Usage: python scripts/market-briefing.py [--index VNINDEX]
Output: JSON to stdout with sections: market, movers, macro, commodities, funds
"""

import argparse
import json
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(description="Market briefing data collector")
    parser.add_argument("--index", default="VNINDEX", help="Market index: VNINDEX, HNX, VN30")
    args = parser.parse_args()

    result = {"index": args.index, "timestamp": datetime.now().isoformat()}

    from claude_finance_kit import Commodity, Fund, Macro, Market

    market = Market(args.index)

    try:
        pe = market.pe(duration="5Y")
        result["pe_history"] = {
            "current": round(float(pe.iloc[-1]["pe"]), 2) if not pe.empty else None,
            "avg_5y": round(float(pe["pe"].mean()), 2) if not pe.empty else None,
            "last_30": json.loads(pe.tail(30).to_json(orient="records", date_format="iso")) if not pe.empty else [],
        }
    except Exception as e:
        result["pe_history"] = {"error": str(e)}

    try:
        result["top_gainers"] = market.top_gainer(limit=10).to_dict(orient="records")
    except Exception as e:
        result["top_gainers"] = {"error": str(e)}

    try:
        result["top_losers"] = market.top_loser(limit=10).to_dict(orient="records")
    except Exception as e:
        result["top_losers"] = {"error": str(e)}

    try:
        result["top_liquidity"] = market.top_liquidity(limit=10).to_dict(orient="records")
    except Exception as e:
        result["top_liquidity"] = {"error": str(e)}

    macro = Macro()
    for name, fn in [("gdp", lambda: macro.gdp(period="quarter")),
                     ("cpi", lambda: macro.cpi(length="2Y", period="month")),
                     ("interest_rate", lambda: macro.interest_rate()),
                     ("exchange_rate", lambda: macro.exchange_rate()),
                     ("fdi", lambda: macro.fdi(period="month"))]:
        try:
            df = fn()
            result[name] = df.tail(6).to_dict(orient="records") if not df.empty else []
        except Exception as e:
            result[name] = {"error": str(e)}

    commodity = Commodity()
    for name, fn in [("gold", commodity.gold), ("oil", commodity.oil), ("steel", commodity.steel)]:
        try:
            df = fn(length="3M")
            result[f"commodity_{name}"] = df.tail(5).to_dict(orient="records") if not df.empty else []
        except Exception as e:
            result[f"commodity_{name}"] = {"error": str(e)}

    try:
        fund = Fund()
        listing = fund.listing(fund_type="STOCK")
        result["funds"] = listing.head(10).to_dict(orient="records") if not listing.empty else []
    except Exception as e:
        result["funds"] = {"error": str(e)}

    print(json.dumps(result, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
