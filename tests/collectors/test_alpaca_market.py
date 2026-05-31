from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from stock_agent.collectors.alpaca_market import AlpacaMarketClient


def test_alpaca_market_fetches_daily_bars_with_auth_headers() -> None:
    calls: list[tuple[str, dict[str, str]]] = []

    def fake_get(url: str, headers: dict[str, str]) -> dict:
        calls.append((url, headers))
        return {
            "bars": {
                "AAPL": [
                    {
                        "t": "2026-05-29T04:00:00Z",
                        "o": 190.0,
                        "h": 195.0,
                        "l": 188.5,
                        "c": 194.2,
                        "v": 123456789,
                    }
                ]
            }
        }

    client = AlpacaMarketClient(
        api_key="key",
        secret_key="secret",
        http_get=fake_get,
    )

    prices = client.get_daily_bars(["AAPL"], start="2026-05-29", end="2026-05-30")

    parsed = urlparse(calls[0][0])
    params = parse_qs(parsed.query)
    assert parsed.scheme == "https"
    assert parsed.netloc == "data.alpaca.markets"
    assert parsed.path == "/v2/stocks/bars"
    assert params["symbols"] == ["AAPL"]
    assert params["timeframe"] == ["1Day"]
    assert params["start"] == ["2026-05-29"]
    assert params["end"] == ["2026-05-30"]
    assert calls[0][1] == {
        "APCA-API-KEY-ID": "key",
        "APCA-API-SECRET-KEY": "secret",
    }

    assert len(prices) == 1
    assert prices[0].ticker == "AAPL"
    assert prices[0].trading_date == "2026-05-29"
    assert prices[0].open == 190.0
    assert prices[0].high == 195.0
    assert prices[0].low == 188.5
    assert prices[0].close == 194.2
    assert prices[0].volume == 123456789
    assert prices[0].provider == "alpaca"
