from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from stock_agent.collectors.alpha_vantage import AlphaVantageClient


def test_alpha_vantage_fetches_daily_adjusted_with_api_key() -> None:
    calls: list[tuple[str, dict[str, str]]] = []

    def fake_get(url: str, headers: dict[str, str]) -> dict:
        calls.append((url, headers))
        return {"Meta Data": {"2. Symbol": "AAPL"}}

    client = AlphaVantageClient(api_key="demo", http_get=fake_get)

    payload = client.get_daily_adjusted("AAPL")

    parsed = urlparse(calls[0][0])
    params = parse_qs(parsed.query)
    assert parsed.scheme == "https"
    assert parsed.netloc == "www.alphavantage.co"
    assert parsed.path == "/query"
    assert params["function"] == ["TIME_SERIES_DAILY_ADJUSTED"]
    assert params["symbol"] == ["AAPL"]
    assert params["apikey"] == ["demo"]
    assert params["outputsize"] == ["compact"]
    assert calls[0][1] == {}
    assert payload == {"Meta Data": {"2. Symbol": "AAPL"}}
