from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from stock_agent.collectors.gdelt import GdeltClient


def test_gdelt_search_normalizes_articles_and_query_parameters() -> None:
    calls: list[tuple[str, dict[str, str]]] = []

    def fake_get(url: str, headers: dict[str, str]) -> dict:
        calls.append((url, headers))
        return {
            "articles": [
                {
                    "url": "https://example.com/nvidia-ai",
                    "title": "Nvidia suppliers rally on AI infrastructure demand",
                    "seendate": "20260531T140000Z",
                    "domain": "example.com",
                    "sourceCountry": "US",
                }
            ]
        }

    client = GdeltClient(http_get=fake_get)

    articles = client.search_articles("NVIDIA AI infrastructure", max_records=5)

    parsed = urlparse(calls[0][0])
    params = parse_qs(parsed.query)
    assert parsed.scheme == "https"
    assert parsed.netloc == "api.gdeltproject.org"
    assert parsed.path == "/api/v2/doc/doc"
    assert params["query"] == ["NVIDIA AI infrastructure"]
    assert params["format"] == ["json"]
    assert params["maxrecords"] == ["5"]

    assert len(articles) == 1
    assert articles[0].external_id.startswith("gdelt:")
    assert articles[0].url == "https://example.com/nvidia-ai"
    assert articles[0].title == "Nvidia suppliers rally on AI infrastructure demand"
    assert articles[0].published_at == "20260531T140000Z"
    assert articles[0].source_domain == "example.com"
    assert articles[0].source_country == "US"
