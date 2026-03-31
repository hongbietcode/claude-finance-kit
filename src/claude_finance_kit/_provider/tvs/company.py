"""TVS company module: overview only."""

import logging
import re

import pandas as pd

from claude_finance_kit._internal.http_client import send_request
from claude_finance_kit._internal.transform import clean_html_dict
from claude_finance_kit._internal.user_agent import get_headers
from claude_finance_kit._provider.tvs.const import _BASE_URL

logger = logging.getLogger(__name__)


def _camel_to_snake(name: str) -> str:
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


class TVSCompany:
    """Fetches company overview from TVS."""

    DATA_SOURCE = "TVS"

    def __init__(self) -> None:
        self._headers = get_headers(data_source="TVS", random_agent=True)

    def company_overview(self, symbol: str) -> pd.DataFrame:
        url = f"{_BASE_URL}Dashboard/GetComanyInfo?ticker={symbol.upper()}"
        json_data = send_request(
            url=url, headers=self._headers, method="GET",
        )
        if not json_data:
            raise ValueError(f"No company data found for '{symbol}'.")

        df = pd.DataFrame([json_data] if isinstance(json_data, dict) else json_data)
        df.columns = [_camel_to_snake(c) for c in df.columns]
        df = df.rename(columns={"ticker": "symbol"}, errors="ignore")

        dict_data = df.iloc[0].to_dict()
        clean = clean_html_dict(dict_data)
        df = pd.DataFrame([clean])

        df.attrs["symbol"] = symbol.upper()
        df.attrs["source"] = self.DATA_SOURCE
        return df
