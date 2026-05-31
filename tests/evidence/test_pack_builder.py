from __future__ import annotations

from stock_agent.evidence.pack_builder import (
    EvidencePackBuilder,
    FilingEvidence,
    NewsEvidence,
    PriceFeatures,
)


def test_pack_builder_creates_compact_pack_without_full_article_body() -> None:
    builder = EvidencePackBuilder(max_news_per_ticker=2, max_filings_per_ticker=1)
    news = [
        NewsEvidence(
            id="news_1",
            ticker="NVDA",
            title="Nvidia suppliers rally",
            url="https://example.com/nvidia",
            source_domain="example.com",
            source_country="US",
            published_at="2026-05-31T14:00:00Z",
            snippet="AI infrastructure demand rises.",
            body="THIS_FULL_ARTICLE_BODY_MUST_NOT_APPEAR_IN_THE_EVIDENCE_PACK",
            source_quality=80,
        )
    ]
    filings = [
        FilingEvidence(
            id="sec_1",
            ticker="NVDA",
            form="8-K",
            filed_at="2026-05-31",
            summary="New material agreement disclosed.",
        )
    ]

    pack = builder.build(
        report_date="2026-05-31",
        universe=["NVDA"],
        market_context={"sp500_return_1d": 0.004},
        price_features=[
            PriceFeatures(
                ticker="NVDA",
                features={"return_1d": 0.052, "volume_zscore_20d": 1.7},
            )
        ],
        news=news,
        filings=filings,
    )

    ticker_evidence = pack["ticker_evidence"][0]
    assert ticker_evidence["ticker"] == "NVDA"
    assert ticker_evidence["price_features"] == {
        "return_1d": 0.052,
        "volume_zscore_20d": 1.7,
    }
    assert ticker_evidence["news"] == [
        {
            "id": "news_1",
            "title": "Nvidia suppliers rally",
            "source": "example.com",
            "source_country": "US",
            "published_at": "2026-05-31T14:00:00Z",
            "summary": "Nvidia suppliers rally - AI infrastructure demand rises.",
            "url": "https://example.com/nvidia",
        }
    ]
    assert "THIS_FULL_ARTICLE_BODY" not in str(pack)


def test_pack_builder_dedupes_news_and_caps_evidence_per_ticker() -> None:
    builder = EvidencePackBuilder(max_news_per_ticker=2, max_filings_per_ticker=1)
    duplicate = NewsEvidence(
        id="news_duplicate",
        ticker="NVDA",
        title="Nvidia suppliers rally",
        url="https://example.com/nvidia?utm_source=feed",
        source_domain="example.com",
        source_country="US",
        published_at="2026-05-31T14:00:00Z",
        snippet="AI infrastructure demand rises.",
        body="Same body",
        source_quality=80,
    )
    original = NewsEvidence(
        id="news_original",
        ticker="NVDA",
        title="nvidia suppliers rally",
        url="https://example.com/nvidia",
        source_domain="example.com",
        source_country="US",
        published_at="2026-05-31T14:05:00Z",
        snippet="ai infrastructure demand rises.",
        body="same body",
        source_quality=70,
    )
    higher_quality = NewsEvidence(
        id="news_quality",
        ticker="NVDA",
        title="Supplier order book expands",
        url="https://trusted.example.com/nvidia-orders",
        source_domain="trusted.example.com",
        source_country="US",
        published_at="2026-05-31T13:00:00Z",
        snippet="Large order book expansion reported.",
        body="Different body 1",
        source_quality=95,
    )
    lower_ranked = NewsEvidence(
        id="news_low",
        ticker="NVDA",
        title="Minor commentary",
        url="https://low.example.com/nvidia",
        source_domain="low.example.com",
        source_country="US",
        published_at="2026-05-31T15:00:00Z",
        snippet="Less relevant commentary.",
        body="Different body 2",
        source_quality=10,
    )

    pack = builder.build(
        report_date="2026-05-31",
        universe=["NVDA"],
        market_context={},
        price_features=[PriceFeatures(ticker="NVDA", features={"return_1d": 0.05})],
        news=[duplicate, original, higher_quality, lower_ranked],
        filings=[
            FilingEvidence(
                id="sec_form4",
                ticker="NVDA",
                form="4",
                filed_at="2026-05-31",
                summary="Insider transaction.",
            ),
            FilingEvidence(
                id="sec_8k",
                ticker="NVDA",
                form="8-K",
                filed_at="2026-05-30",
                summary="Material event.",
            ),
        ],
    )

    ticker_evidence = pack["ticker_evidence"][0]
    assert [item["id"] for item in ticker_evidence["news"]] == [
        "news_quality",
        "news_duplicate",
    ]
    assert [item["id"] for item in ticker_evidence["filings"]] == ["sec_8k"]


def test_pack_builder_enforces_report_ticker_budget_by_price_movement() -> None:
    builder = EvidencePackBuilder(max_tickers=1, max_news_per_ticker=1)

    pack = builder.build(
        report_date="2026-05-31",
        universe=["AAPL", "NVDA"],
        market_context={},
        price_features=[
            PriceFeatures(ticker="AAPL", features={"return_1d": 0.01}),
            PriceFeatures(ticker="NVDA", features={"return_1d": -0.12}),
        ],
        news=[
            NewsEvidence(
                id="news_aapl",
                ticker="AAPL",
                title="Apple quiet day",
                url="https://example.com/aapl",
                source_domain="example.com",
                source_country="US",
                published_at="2026-05-31T14:00:00Z",
                snippet="Small move.",
                body="AAPL body",
                source_quality=50,
            ),
            NewsEvidence(
                id="news_nvda",
                ticker="NVDA",
                title="Nvidia sharp move",
                url="https://example.com/nvda",
                source_domain="example.com",
                source_country="US",
                published_at="2026-05-31T14:00:00Z",
                snippet="Large move.",
                body="NVDA body",
                source_quality=50,
            ),
        ],
        filings=[],
    )

    assert [item["ticker"] for item in pack["ticker_evidence"]] == ["NVDA"]
