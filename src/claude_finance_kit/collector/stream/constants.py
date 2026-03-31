"""Constants for VPS WebSocket stream data types and groupings."""

AVAILABLE_DATA_TYPES: dict[str, str] = {
    "index": "Index data (VN-Index, VN30, HNX-Index, etc.)",
    "aggregatemarket": "Aggregate market statistics (volume, value, advances, declines)",
    "aggregateps": "Aggregate derivatives statistics",
    "aggregatecw": "Aggregate covered warrant statistics",
    "aggregateetf": "Aggregate ETF statistics",
    "stock": "Individual stock price data",
    "stockps": "Stock price-size data (including derivatives)",
    "board": "Order book depth data (HOSE equities)",
    "boardps": "Order book depth data (derivatives)",
    "soddlot": "Odd-lot trading data",
    "aggregateforeigngroup": "Foreign trading by proprietary groups",
    "aggregateforeignmarket": "Foreign trading by market",
    "spt": "Special/Put-through transactions",
    "psfsell": "Proprietary securities firm sell data",
    "regs": "Registration/subscription responses",
}

DATA_TYPE_GROUPS: dict[str, list[str]] = {
    "market": ["index", "aggregatemarket", "aggregateps", "aggregatecw", "aggregateetf"],
    "stocks": ["stock", "stockps", "board", "boardps"],
    "foreign": ["aggregateforeigngroup", "aggregateforeignmarket"],
    "transactions": ["spt", "soddlot"],
    "all": list(AVAILABLE_DATA_TYPES.keys()),
}

ESSENTIAL_DATA_TYPES: list[str] = ["stock", "stockps", "board", "index", "aggregatemarket"]

USE_CASE_DATA_TYPES: dict[str, list[str]] = {
    "basic_monitoring": ["stock", "stockps", "index"],
    "orderbook_analysis": ["board", "boardps"],
    "foreign_flow": ["aggregateforeigngroup", "aggregateforeignmarket"],
    "market_overview": ["index", "aggregatemarket", "aggregatecw", "aggregateetf"],
    "derivatives": ["stockps", "boardps", "aggregateps"],
}


def get_data_type_description(data_type: str) -> str:
    """Return the description for a data type, or 'Unknown data type'."""
    return AVAILABLE_DATA_TYPES.get(data_type, "Unknown data type")


def validate_data_types(data_types: list[str]) -> tuple[list[str], list[str]]:
    """Split data_types into (valid, invalid) lists.

    Args:
        data_types: List of data type strings to validate.

    Returns:
        Tuple of (valid_types, invalid_types).
    """
    if not data_types:
        return [], []
    valid = [t for t in data_types if t in AVAILABLE_DATA_TYPES]
    invalid = [t for t in data_types if t not in AVAILABLE_DATA_TYPES]
    return valid, invalid


def expand_data_type_group(group_or_types: list[str]) -> list[str]:
    """Expand group names to individual data type strings, preserving order and deduplicating.

    Args:
        group_or_types: List that may contain group names or individual type strings.

    Returns:
        Deduplicated list of individual data type strings.
    """
    expanded: list[str] = []
    seen: set[str] = set()
    for item in group_or_types:
        items = DATA_TYPE_GROUPS.get(item, [item])
        for t in items:
            if t not in seen:
                seen.add(t)
                expanded.append(t)
    return expanded
