from __future__ import annotations

import hashlib
from dataclasses import dataclass
from urllib.parse import urlencode

from stock_agent.collectors._http import JsonHttpGet, get_json


@dataclass(frozen=True)
class NewsArticle:
    external_id: str
    url: str
    title: str
    published_at: str
    source_domain: str
    source_country: str | None


class GdeltClient:
    api_url = "https://api.gdeltproject.org/api/v2/doc/doc"

    def __init__(self, http_get: JsonHttpGet | None = None) -> None:
        self.http_get = http_get or get_json

    def search_articles(self, query: str, max_records: int = 25) -> list[NewsArticle]:
        params = urlencode(
            {
                "query": query,
                "mode": "ArtList",
                "format": "json",
                "maxrecords": str(max_records),
                "sort": "hybridrel",
            }
        )
        payload = self.http_get(f"{self.api_url}?{params}", {})
        articles = payload.get("articles", [])

        normalized: list[NewsArticle] = []
        for article in articles:
            url = str(article.get("url", "")).strip()
            if not url:
                continue
            normalized.append(
                NewsArticle(
                    external_id=f"gdelt:{_stable_hash(url)}",
                    url=url,
                    title=str(article.get("title", "")).strip(),
                    published_at=str(article.get("seendate", "")).strip(),
                    source_domain=str(article.get("domain", "")).strip(),
                    source_country=article.get("sourceCountry"),
                )
            )
        return normalized


def _stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
