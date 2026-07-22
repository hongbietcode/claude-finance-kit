"""Market constants: indices, sectors, exchanges."""

INDICES_INFO: dict = {
    "VNINDEX": {
        "name": "VNINDEX",
        "description": "Chỉ số đại diện cho cổ phiếu niêm yết trên HOSE",
        "full_name": "VN-Index",
        "group": "Market Indices",
        "index_id": None,
    },
    "HNXINDEX": {
        "name": "HNXINDEX",
        "description": "Chỉ số đại diện cho cổ phiếu niêm yết trên HNX",
        "full_name": "HNX Index",
        "group": "Market Indices",
        "index_id": None,
    },
    "UPCOMINDEX": {
        "name": "UPCOMINDEX",
        "description": "Chỉ số đại diện cho cổ phiếu đăng ký giao dịch trên UPCOM",
        "full_name": "UPCOM Index",
        "group": "Market Indices",
        "index_id": None,
    },
    "VN30": {
        "name": "VN30",
        "description": "30 cổ phiếu vốn hóa lớn nhất & thanh khoản tốt nhất HOSE",
        "full_name": "VN30 Index",
        "group": "HOSE Indices",
        "index_id": 5,
    },
    "VNMID": {
        "name": "VNMID",
        "description": "Mid-Cap Index - nhóm cổ phiếu vốn hóa trung bình",
        "full_name": "VNMidCap Index",
        "group": "HOSE Indices",
        "index_id": 6,
    },
    "VNSML": {
        "name": "VNSML",
        "description": "Small-Cap Index - nhóm cổ phiếu vốn hóa nhỏ",
        "full_name": "VNSmallCap Index",
        "group": "HOSE Indices",
        "index_id": 7,
    },
    "VN100": {
        "name": "VN100",
        "description": "100 cổ phiếu có vốn hoá lớn nhất HOSE",
        "full_name": "VN100 Index",
        "group": "HOSE Indices",
        "index_id": 8,
    },
    "VNALL": {
        "name": "VNALL",
        "description": "Tất cả cổ phiếu trên HOSE và HNX",
        "full_name": "VNAll Index",
        "group": "HOSE Indices",
        "index_id": 9,
    },
    "VNSI": {
        "name": "VNSI",
        "description": "Vietnam Small-Cap Index",
        "full_name": "VNSI Index",
        "group": "HOSE Indices",
        "index_id": 21,
    },
    "VNIT": {
        "name": "VNIT",
        "description": "Công nghệ thông tin",
        "full_name": "Information Technology Sector Index",
        "group": "Sector Indices",
        "index_id": 10,
        "sector_id": 159,
    },
    "VNIND": {
        "name": "VNIND",
        "description": "Công nghiệp",
        "full_name": "Industrials Sector Index",
        "group": "Sector Indices",
        "index_id": 11,
        "sector_id": 155,
    },
    "VNCONS": {
        "name": "VNCONS",
        "description": "Hàng tiêu dùng",
        "full_name": "Consumer Staples Index",
        "group": "Sector Indices",
        "index_id": 12,
        "sector_id": 130,
    },
    "VNCOND": {
        "name": "VNCOND",
        "description": "Hàng tiêu dùng thiết yếu",
        "full_name": "Consumer Discretionary Sector Index",
        "group": "Sector Indices",
        "index_id": 13,
        "sector_id": 133,
    },
    "VNHEAL": {
        "name": "VNHEAL",
        "description": "Chăm sóc sức khoẻ",
        "full_name": "Health Care Sector Index",
        "group": "Sector Indices",
        "index_id": 14,
        "sector_id": 135,
    },
    "VNENE": {
        "name": "VNENE",
        "description": "Năng lượng",
        "full_name": "Energy Sector Index",
        "group": "Sector Indices",
        "index_id": 15,
        "sector_id": 154,
    },
    "VNUTI": {
        "name": "VNUTI",
        "description": "Dịch vụ tiện ích",
        "full_name": "Utilities Sector Index",
        "group": "Sector Indices",
        "index_id": 16,
        "sector_id": 150,
    },
    "VNREAL": {
        "name": "VNREAL",
        "description": "Bất động sản",
        "full_name": "Real Estate Sector Index",
        "group": "Sector Indices",
        "index_id": 17,
        "sector_id": 166,
    },
    "VNFIN": {
        "name": "VNFIN",
        "description": "Tài chính",
        "full_name": "Financials Sector Index",
        "group": "Sector Indices",
        "index_id": 18,
        "sector_id": 138,
    },
    "VNMAT": {
        "name": "VNMAT",
        "description": "Nguyên vật liệu",
        "full_name": "Materials Sector Index",
        "group": "Sector Indices",
        "index_id": 19,
        "sector_id": 143,
    },
    "VNDIAMOND": {
        "name": "VNDIAMOND",
        "description": (
            "Chỉ số các cổ phiếu có triển vọng lớn của doanh "
            "nghiệp đầu ngành thuộc các lĩnh vực khác nhau"
        ),
        "full_name": "Vietnam Diamond Index",
        "group": "Investment Indices",
        "index_id": 2,
    },
    "VNFINLEAD": {
        "name": "VNFINLEAD",
        "description": (
            "Chỉ số của các cổ phiếu thuộc nhóm ngành tài chính "
            "đầu ngành (ngân hàng, chứng khoán, bảo hiểm)"
        ),
        "full_name": "Vietnam Leading Financial Index",
        "group": "Investment Indices",
        "index_id": 3,
    },
    "VNFINSELECT": {
        "name": "VNFINSELECT",
        "description": (
            "Chỉ số của các cổ phiếu đại diện cho ngành tài "
            "chính, đến từ những công ty chứng khoán, bảo hiểm"
        ),
        "full_name": "Vietnam Financial Select Sector Index",
        "group": "Investment Indices",
        "index_id": 4,
    },
    "VNX50": {
        "name": "VNX50",
        "description": (
            "50 cổ phiếu vốn hóa lớn nhất trên toàn bộ thị "
            "trường HOSE và HNX"
        ),
        "full_name": "VNX50 Index",
        "group": "VNX Indices",
        "index_id": 4,
    },
    "VNXALL": {
        "name": "VNXALL",
        "description": "Tất cả cổ phiếu trên toàn bộ thị trường HOSE và HNX",
        "full_name": "VNX All Index",
        "group": "VNX Indices",
        "index_id": 1,
    },
    "HNX30": {
        "name": "HNX30",
        "description": "30 cổ phiếu thanh khoản cao trên HNX",
        "full_name": "HNX30 Index",
        "group": "HNX Indices",
        "index_id": None,
    },
    "HNXFIN": {
        "name": "HNXFIN",
        "description": "Chỉ số ngành tài chính HNX",
        "full_name": "HNX Financials Index",
        "group": "HNX Indices",
        "index_id": None,
    },
    "HNXCON": {
        "name": "HNXCON",
        "description": "Chỉ số ngành xây dựng HNX",
        "full_name": "HNX Construction Index",
        "group": "HNX Indices",
        "index_id": None,
    },
    "HNXLCAP": {
        "name": "HNXLCAP",
        "description": "Chỉ số cổ phiếu vốn hóa lớn HNX",
        "full_name": "HNX Large Cap Index",
        "group": "HNX Indices",
        "index_id": None,
    },
    "HNXMAN": {
        "name": "HNXMAN",
        "description": "Chỉ số ngành công nghiệp HNX",
        "full_name": "HNX Manufacturing Index",
        "group": "HNX Indices",
        "index_id": None,
    },
    "HNXMSCAP": {
        "name": "HNXMSCAP",
        "description": "Chỉ số cổ phiếu vốn hóa vừa và nhỏ HNX",
        "full_name": "HNX Mid/Small Cap Index",
        "group": "HNX Indices",
        "index_id": None,
    },
    "UPCOMLAR": {
        "name": "UPCOMLAR",
        "description": "Chỉ số cổ phiếu vốn hóa lớn UPCOM",
        "full_name": "UPCOM Large Index",
        "group": "UPCOM Indices",
        "index_id": None,
    },
    "UPCOMMID": {
        "name": "UPCOMMID",
        "description": "Chỉ số cổ phiếu vốn hóa vừa UPCOM",
        "full_name": "UPCOM Medium Index",
        "group": "UPCOM Indices",
        "index_id": None,
    },
    "UPCOMSML": {
        "name": "UPCOMSML",
        "description": "Chỉ số cổ phiếu vốn hóa nhỏ UPCOM",
        "full_name": "UPCOM Small Index",
        "group": "UPCOM Indices",
        "index_id": None,
    },
}

INDICES_MAP: dict[str, int | None] = {
    sym: info["index_id"] for sym, info in INDICES_INFO.items()
}

INDEX_ALIASES: dict[str, str] = {
    "VNI": "VNINDEX",
    "HNX": "HNXINDEX",
    "UPCOM": "UPCOMINDEX",
    "VNMIDCAP": "VNMID",
    "VNSMALLCAP": "VNSML",
    "VNALLSHARE": "VNALL",
    "HNXFINANCIALS": "HNXFIN",
    "HNXCONSTRUCTION": "HNXCON",
    "HNXLARGECAP": "HNXLCAP",
    "HNXMANUFACTURING": "HNXMAN",
    "HNXMIDSMALLCAP": "HNXMSCAP",
}

INDEX_GROUPS: dict[str, list[str]] = {
    "Market Indices": ["VNINDEX", "HNXINDEX", "UPCOMINDEX"],
    "HOSE Indices": ["VN30", "VNMID", "VNSML", "VN100", "VNALL", "VNSI"],
    "Sector Indices": [
        "VNIT", "VNIND", "VNCONS", "VNCOND", "VNHEAL",
        "VNENE", "VNUTI", "VNREAL", "VNFIN", "VNMAT",
    ],
    "Investment Indices": ["VNDIAMOND", "VNFINLEAD", "VNFINSELECT"],
    "VNX Indices": ["VNX50", "VNXALL"],
    "HNX Indices": ["HNX30", "HNXFIN", "HNXCON", "HNXLCAP", "HNXMAN", "HNXMSCAP"],
    "UPCOM Indices": ["UPCOMLAR", "UPCOMMID", "UPCOMSML"],
}

SECTOR_IDS: dict[int, str] = {
    126: "Dịch vụ viễn thông",
    130: "Hàng tiêu dùng",
    133: "Hàng tiêu dùng thiết yếu",
    135: "Chăm sóc sức khoẻ",
    138: "Tài chính",
    143: "Nguyên vật liệu",
    150: "Dịch vụ tiện ích",
    154: "Năng lượng",
    155: "Công nghiệp",
    159: "Công nghệ thông tin",
    166: "Bất động sản",
}

EXCHANGES: dict[str, str] = {
    "HOSE": "Sở giao dịch Hồ Chí Minh (HOSE)",
    "HNX": "Sở giao dịch Hà Nội (HNX)",
    "UPCOM": "Sở giao dịch Hà Nội (UPCOM)",
}
