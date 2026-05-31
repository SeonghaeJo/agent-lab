from __future__ import annotations

from urllib.parse import urlencode

from stock_agent.collectors._http import JsonHttpGet, get_json
from stock_agent.storage.schemas import TickerPrice


class AlpacaMarketClient:
    bars_url = "https://data.alpaca.markets/v2/stocks/bars"

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        http_get: JsonHttpGet | None = None,
    ) -> None:
        self.api_key = api_key
        self.secret_key = secret_key
        self.http_get = http_get or get_json

    def get_daily_bars(
        self,
        symbols: list[str],
        start: str,
        end: str,
    ) -> list[TickerPrice]:
        params = urlencode(
            {
                "symbols": ",".join(symbols),
                "timeframe": "1Day",
                "start": start,
                "end": end,
            }
        )
        payload = self.http_get(f"{self.bars_url}?{params}", self._headers())
        bars_by_symbol = payload.get("bars", {})

        prices: list[TickerPrice] = []
        for symbol in symbols:
            for bar in bars_by_symbol.get(symbol, []):
                prices.append(
                    TickerPrice(
                        ticker=symbol,
                        trading_date=str(bar["t"])[:10],
                        open=float(bar["o"]),
                        high=float(bar["h"]),
                        low=float(bar["l"]),
                        close=float(bar["c"]),
                        volume=int(bar["v"]),
                        provider="alpaca",
                    )
                )
        return prices

    def _headers(self) -> dict[str, str]:
        return {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key,
        }
