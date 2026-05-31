from __future__ import annotations

from stock_agent.models.base import AnalystReport, CandidatePrediction, CostMetadata
from stock_agent.reports.synthesizer import synthesize_reports


def _candidate(
    *,
    ticker: str,
    direction: str,
    probability: float,
    thesis: str,
    horizon_days: int = 5,
    catalysts: list[str] | None = None,
    risks: list[str] | None = None,
) -> CandidatePrediction:
    return CandidatePrediction(
        ticker=ticker,
        horizon_days=horizon_days,
        direction=direction,
        probability=probability,
        confidence="medium",
        thesis=thesis,
        bull_case=f"{ticker} bull case",
        bear_case=f"{ticker} bear case",
        catalysts=catalysts or ["sector momentum"],
        risks=risks or ["valuation"],
        evidence_ids=[f"news_{ticker.lower()}"],
        review_after="2026-06-07",
    )


def _report(model_id: str, candidates: list[CandidatePrediction]) -> AnalystReport:
    return AnalystReport(
        model_id=model_id,
        report_date="2026-05-31",
        analyst_role="fast_analyst",
        market_view="risk-on",
        top_long_candidates=candidates,
        avoid_or_short_watch=[],
        questions_for_user=[f"Question from {model_id}?"],
        cost=CostMetadata.zero(),
        prompt_hash=f"hash-{model_id}",
    )


def test_synthesize_reports_detects_consensus_and_disagreement() -> None:
    result = synthesize_reports(
        [
            _report(
                "model/a",
                [
                    _candidate(
                        ticker="NVDA",
                        direction="up",
                        probability=0.62,
                        thesis="AI demand remains strong.",
                        catalysts=["AI infrastructure"],
                        risks=["valuation"],
                    ),
                    _candidate(
                        ticker="AAPL",
                        direction="up",
                        probability=0.57,
                        thesis="Services growth offsets hardware softness.",
                    ),
                ],
            ),
            _report(
                "model/b",
                [
                    _candidate(
                        ticker="NVDA",
                        direction="up",
                        probability=0.68,
                        thesis="Supplier checks support near-term momentum.",
                        catalysts=["supplier orders"],
                        risks=["export controls"],
                    ),
                    _candidate(
                        ticker="AAPL",
                        direction="down",
                        probability=0.55,
                        thesis="Hardware demand risk matters more near term.",
                    ),
                ],
            ),
        ]
    )

    assert result.report_date == "2026-05-31"
    assert result.model_ids == ["model/a", "model/b"]
    assert len(result.consensus) == 1
    assert result.consensus[0].ticker == "NVDA"
    assert result.consensus[0].direction == "up"
    assert result.consensus[0].models == ["model/a", "model/b"]
    assert result.consensus[0].average_probability == 0.65
    assert result.consensus[0].catalysts == ["AI infrastructure", "supplier orders"]
    assert result.consensus[0].risks == ["export controls", "valuation"]

    assert len(result.disagreements) == 1
    assert result.disagreements[0].ticker == "AAPL"
    assert result.disagreements[0].directions_by_model == {
        "model/a": "up",
        "model/b": "down",
    }
    assert result.disagreements[0].theses_by_model == {
        "model/a": "Services growth offsets hardware softness.",
        "model/b": "Hardware demand risk matters more near term.",
    }


def test_synthesize_reports_preserves_ticker_theses_and_user_questions() -> None:
    result = synthesize_reports(
        [
            _report(
                "model/a",
                [
                    _candidate(
                        ticker="MSFT",
                        direction="up",
                        probability=0.58,
                        thesis="Cloud demand is resilient.",
                    )
                ],
            )
        ]
    )

    assert result.ticker_theses[0].ticker == "MSFT"
    assert result.ticker_theses[0].model_id == "model/a"
    assert result.ticker_theses[0].evidence_ids == ["news_msft"]
    assert result.questions_for_user == ["Question from model/a?"]
