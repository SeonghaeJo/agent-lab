from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from stock_agent.evidence.dedupe import DocumentFingerprintInput, fingerprint_document
from stock_agent.evidence.summarizer import summarize_news


@dataclass(frozen=True)
class NewsEvidence:
    id: str
    ticker: str
    title: str
    url: str
    source_domain: str
    source_country: str | None
    published_at: str
    snippet: str
    body: str
    source_quality: int


@dataclass(frozen=True)
class FilingEvidence:
    id: str
    ticker: str
    form: str
    filed_at: str
    summary: str


@dataclass(frozen=True)
class PriceFeatures:
    ticker: str
    features: dict[str, float]


class EvidencePackBuilder:
    def __init__(
        self,
        max_tickers: int | None = None,
        max_news_per_ticker: int = 3,
        max_filings_per_ticker: int = 2,
    ) -> None:
        self.max_tickers = max_tickers
        self.max_news_per_ticker = max_news_per_ticker
        self.max_filings_per_ticker = max_filings_per_ticker

    def build(
        self,
        report_date: str,
        universe: list[str],
        market_context: dict[str, Any],
        price_features: list[PriceFeatures],
        news: list[NewsEvidence],
        filings: list[FilingEvidence],
    ) -> dict[str, Any]:
        prices_by_ticker = {item.ticker: item.features for item in price_features}
        selected_tickers = self._rank_tickers(universe, prices_by_ticker)

        ticker_evidence = []
        for ticker in selected_tickers:
            ticker_news = [item for item in news if item.ticker == ticker]
            ticker_filings = [item for item in filings if item.ticker == ticker]
            ticker_evidence.append(
                {
                    "ticker": ticker,
                    "price_features": prices_by_ticker.get(ticker, {}),
                    "news": [
                        _news_to_pack_item(item)
                        for item in self._select_news(ticker_news)
                    ],
                    "filings": [
                        _filing_to_pack_item(item)
                        for item in self._select_filings(ticker_filings)
                    ],
                }
            )

        return {
            "report_date": report_date,
            "universe": universe,
            "market_context": market_context,
            "ticker_evidence": ticker_evidence,
        }

    def _rank_tickers(
        self,
        universe: list[str],
        prices_by_ticker: dict[str, dict[str, float]],
    ) -> list[str]:
        ranked = sorted(
            universe,
            key=lambda ticker: (
                abs(float(prices_by_ticker.get(ticker, {}).get("return_1d", 0.0))),
                ticker,
            ),
            reverse=True,
        )
        if self.max_tickers is None:
            return ranked
        return ranked[: self.max_tickers]

    def _select_news(self, news: list[NewsEvidence]) -> list[NewsEvidence]:
        unique_by_fingerprint: dict[str, NewsEvidence] = {}
        for item in news:
            fingerprint = fingerprint_document(
                DocumentFingerprintInput(
                    url=item.url,
                    title=item.title,
                    body=item.body or item.snippet,
                )
            )
            unique_by_fingerprint.setdefault(fingerprint, item)

        ranked = sorted(
            unique_by_fingerprint.values(),
            key=lambda item: (
                item.source_quality,
                _parse_sortable_date(item.published_at),
                item.id,
            ),
            reverse=True,
        )
        return ranked[: self.max_news_per_ticker]

    def _select_filings(self, filings: list[FilingEvidence]) -> list[FilingEvidence]:
        ranked = sorted(
            filings,
            key=lambda item: (
                _filing_importance(item.form),
                _parse_sortable_date(item.filed_at),
                item.id,
            ),
            reverse=True,
        )
        return ranked[: self.max_filings_per_ticker]


def _news_to_pack_item(item: NewsEvidence) -> dict[str, Any]:
    return {
        "id": item.id,
        "title": item.title,
        "source": item.source_domain,
        "source_country": item.source_country,
        "published_at": item.published_at,
        "summary": summarize_news(item.title, item.snippet),
        "url": item.url,
    }


def _filing_to_pack_item(item: FilingEvidence) -> dict[str, Any]:
    return {
        "id": item.id,
        "form": item.form,
        "filed_at": item.filed_at,
        "summary": item.summary,
    }


def _filing_importance(form: str) -> int:
    normalized = form.upper()
    if normalized in {"8-K", "10-Q", "10-K", "S-1"}:
        return 100
    if normalized in {"13F-HR", "SC 13D", "SC 13G"}:
        return 60
    if normalized == "4":
        return 40
    return 10


def _parse_sortable_date(value: str) -> float:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(normalized).timestamp()
    except ValueError:
        try:
            return datetime.strptime(value, "%Y-%m-%d").timestamp()
        except ValueError:
            return 0.0
