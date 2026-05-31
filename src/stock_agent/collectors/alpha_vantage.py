from __future__ import annotations

from urllib.parse import urlencode

from stock_agent.collectors._http import JsonHttpGet, get_json


class AlphaVantageClient:
    api_url = "https://www.alphavantage.co/query"

    def __init__(self, api_key: str, http_get: JsonHttpGet | None = None) -> None:
        self.api_key = api_key
        self.http_get = http_get or get_json

    def get_daily_adjusted(self, symbol: str) -> dict:
        params = urlencode(
            {
                "function": "TIME_SERIES_DAILY_ADJUSTED",
                "symbol": symbol,
                "apikey": self.api_key,
                "outputsize": "compact",
            }
        )
        return self.http_get(f"{self.api_url}?{params}", {})
