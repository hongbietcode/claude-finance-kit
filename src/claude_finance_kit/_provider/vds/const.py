"""VDS (Viet Dragon Securities) API constants and field mappings."""

_BASE_URL = "https://livedragon.vdsc.com.vn/"
_COOKIE_URL = f"{_BASE_URL}general/intradayBoard.rv"
_INTRADAY_URL = f"{_BASE_URL}general/intradaySearch.rv"

_INTRADAY_MAP = {
    "TradeTime": "time",
    "Code": "symbol",
    "MatchedPrice": "price",
    "MatchedVol": "volume",
    "MatchedTotalVol": "total_volume",
    "MatchedChange": "change",
    "AvgPrice": "avg_price",
    "HigPrice": "high",
    "LowPrice": "low",
    "RefPrice": "ref_price",
    "CeiPrice": "ceiling_price",
    "FlrPrice": "floor_price",
    "FloorCode": "exchange",
    "FBuyVol": "foreign_buy_vol",
    "FSellVol": "foreign_sell_vol",
    "BidPrice1": "bid_price_1",
    "BidVol1": "bid_vol_1",
    "BidPrice2": "bid_price_2",
    "BidVol2": "bid_vol_2",
    "BidPrice3": "bid_price_3",
    "BidVol3": "bid_vol_3",
    "OfferPrice1": "ask_price_1",
    "OfferVol1": "ask_vol_1",
    "OfferPrice2": "ask_price_2",
    "OfferVol2": "ask_vol_2",
    "OfferPrice3": "ask_price_3",
    "OfferVol3": "ask_vol_3",
    "AmPm": "session",
}
