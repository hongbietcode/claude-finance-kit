"""Technical Composite Score — compute trend + momentum + volume + volatility scores.

Usage: python scripts/technical-composite-score.py TICKER [--days 200] [--source VCI]
Output: JSON with composite score (0-100), category scores, key indicators, levels

Formula: score = trend(35%) + momentum(30%) + volume(20%) + volatility(15%)
Scale: >70 Bullish | 40-70 Neutral | <40 Bearish
"""

import argparse
import json
from datetime import datetime, timedelta


def main():
    parser = argparse.ArgumentParser(description="Technical composite score calculator")
    parser.add_argument("ticker", help="Stock ticker symbol")
    parser.add_argument("--days", type=int, default=200, help="History days")
    parser.add_argument("--source", default="VCI", help="Data source")
    args = parser.parse_args()

    from claude_finance_kit import Stock
    from claude_finance_kit.core.exceptions import ProviderError
    from claude_finance_kit.ta import Indicator

    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d")

    try:
        stock = Stock(args.ticker, source=args.source)
        df = stock.quote.history(start=start, end=end)
        if df.empty:
            raise ValueError("empty")
    except (ProviderError, Exception):
        stock = Stock(args.ticker, source="KBS")
        df = stock.quote.history(start=start, end=end)

    if df.empty:
        print(json.dumps({"error": "No price data available"}))
        return

    df = df.set_index("time")
    ind = Indicator(df)
    price = float(df["close"].iloc[-1])

    trend_signals = compute_trend(ind, df)
    momentum_signals = compute_momentum(ind)
    volume_signals = compute_volume(ind, df)
    volatility_info = compute_volatility(ind, price)

    composite = (
        trend_signals["score"] * 0.35
        + momentum_signals["score"] * 0.30
        + volume_signals["score"] * 0.20
        + volatility_info["score"] * 0.15
    )

    signal = "BULLISH" if composite > 70 else "BEARISH" if composite < 40 else "NEUTRAL"

    result = {
        "ticker": args.ticker,
        "price": price,
        "signal": signal,
        "composite_score": round(composite, 1),
        "trend": trend_signals,
        "momentum": momentum_signals,
        "volume": volume_signals,
        "volatility": volatility_info,
        "levels": {
            "stop_loss": round(price - volatility_info.get("atr", 0) * 2, 2),
            "target": round(price + volatility_info.get("atr", 0) * 3, 2),
        },
        "timestamp": datetime.now().isoformat(),
    }

    print(json.dumps(result, ensure_ascii=False, default=str))


def compute_trend(ind, df):
    signals = 0
    total = 0
    details = {}

    try:
        sma50 = ind.trend.sma(length=50)
        sma200 = ind.trend.sma(length=200)
        if sma50.dropna().size > 0 and sma200.dropna().size > 0:
            total += 1
            golden = float(sma50.iloc[-1]) > float(sma200.iloc[-1])
            if golden:
                signals += 1
            details["sma_cross"] = "golden" if golden else "death"
    except Exception:
        pass

    try:
        sma200 = ind.trend.sma(length=200)
        if sma200.dropna().size > 0:
            total += 1
            above = float(df["close"].iloc[-1]) > float(sma200.iloc[-1])
            if above:
                signals += 1
            details["above_sma200"] = above
    except Exception:
        pass

    try:
        adx = ind.trend.adx(period=14)
        if not adx.empty:
            adx_val = float(adx.dropna().iloc[-1].iloc[0])
            total += 1
            if adx_val > 25:
                signals += 1
            details["adx"] = round(adx_val, 1)
    except Exception:
        pass

    try:
        st = ind.trend.supertrend(period=10, multiplier=3.0)
        if not st.empty:
            total += 1
            direction = float(st.dropna().iloc[-1].iloc[1])
            if direction > 0:
                signals += 1
            details["supertrend"] = "up" if direction > 0 else "down"
    except Exception:
        pass

    score = (signals / total * 100) if total > 0 else 50
    return {"score": round(score, 1), "signals": signals, "total": total, **details}


def compute_momentum(ind):
    signals = 0
    total = 0
    details = {}

    try:
        rsi = ind.momentum.rsi(length=14)
        if rsi.dropna().size > 0:
            rsi_val = float(rsi.iloc[-1])
            total += 1
            if 40 <= rsi_val <= 70:
                signals += 1
            elif rsi_val < 30:
                signals += 0.5
            details["rsi"] = round(rsi_val, 1)
    except Exception:
        pass

    try:
        macd_df = ind.momentum.macd()
        if not macd_df.empty:
            row = macd_df.dropna().iloc[-1]
            total += 1
            macd_val = float(row.iloc[0])
            signal_val = float(row.iloc[1])
            if macd_val > signal_val:
                signals += 1
            details["macd_above_signal"] = macd_val > signal_val
    except Exception:
        pass

    try:
        stoch = ind.momentum.stoch()
        if not stoch.empty:
            row = stoch.dropna().iloc[-1]
            total += 1
            k = float(row.iloc[0])
            d = float(row.iloc[1])
            if k > d and k < 80:
                signals += 1
            details["stoch_k"] = round(k, 1)
    except Exception:
        pass

    try:
        mfi = ind.volume.mfi(length=14)
        if mfi.dropna().size > 0:
            total += 1
            mfi_val = float(mfi.iloc[-1])
            if mfi_val > 50:
                signals += 1
            details["mfi"] = round(mfi_val, 1)
    except Exception:
        pass

    score = (signals / total * 100) if total > 0 else 50
    return {"score": round(score, 1), "signals": round(signals, 1), "total": total, **details}


def compute_volume(ind, df):
    signals = 0
    total = 0
    details = {}

    try:
        obv = ind.volume.obv()
        if obv.dropna().size > 5:
            total += 1
            obv_trend = float(obv.iloc[-1]) > float(obv.iloc[-5])
            price_trend = float(df["close"].iloc[-1]) > float(df["close"].iloc[-5])
            if obv_trend and price_trend:
                signals += 1
            details["obv_confirms"] = obv_trend == price_trend
    except Exception:
        pass

    try:
        vwap = ind.volume.vwap()
        if vwap.dropna().size > 0:
            total += 1
            above_vwap = float(df["close"].iloc[-1]) > float(vwap.iloc[-1])
            if above_vwap:
                signals += 1
            details["above_vwap"] = above_vwap
    except Exception:
        pass

    try:
        adl = ind.volume.adl()
        if adl.dropna().size > 5:
            total += 1
            adl_rising = float(adl.iloc[-1]) > float(adl.iloc[-5])
            if adl_rising:
                signals += 1
            details["adl_rising"] = adl_rising
    except Exception:
        pass

    score = (signals / total * 100) if total > 0 else 50
    return {"score": round(score, 1), "signals": signals, "total": total, **details}


def compute_volatility(ind, price):
    details = {}

    try:
        atr = ind.volatility.atr(length=14)
        if atr.dropna().size > 0:
            atr_val = float(atr.iloc[-1])
            details["atr"] = round(atr_val, 2)
            details["atr_pct"] = round(atr_val / price * 100, 2)
    except Exception:
        details["atr"] = 0

    try:
        bb = ind.trend.bbands(length=20)
        if not bb.empty:
            row = bb.dropna().iloc[-1]
            bbl = float(row.iloc[0])
            bbu = float(row.iloc[2])
            bb_width = (bbu - bbl) / ((bbu + bbl) / 2) * 100
            details["bb_width"] = round(bb_width, 2)
            details["bb_position"] = round((price - bbl) / (bbu - bbl) * 100, 1) if bbu != bbl else 50
    except Exception:
        pass

    score = 50
    bb_pos = details.get("bb_position", 50)
    if 20 <= bb_pos <= 80:
        score = 70
    elif bb_pos < 20:
        score = 80
    else:
        score = 30

    return {"score": score, **details}


if __name__ == "__main__":
    main()
