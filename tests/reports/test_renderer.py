from __future__ import annotations

from stock_agent.models.base import AnalystReport, CandidatePrediction, CostMetadata
from stock_agent.reports.renderer import DailyReportContext, DailyReportRenderer
from stock_agent.reports.synthesizer import synthesize_reports
from stock_agent.storage.object_store import FileObjectStore


def _report() -> AnalystReport:
    return AnalystReport(
        model_id="model/a",
        report_date="2026-05-31",
        analyst_role="fast_analyst",
        market_view="risk-on",
        top_long_candidates=[
            CandidatePrediction(
                ticker="NVDA",
                horizon_days=5,
                direction="up",
                probability=0.62,
                confidence="medium",
                thesis="AI infrastructure demand supports momentum.",
                bull_case="Demand commentary is strong.",
                bear_case="Valuation is stretched.",
                catalysts=["AI infrastructure"],
                risks=["valuation"],
                evidence_ids=["news_nvda"],
                review_after="2026-06-07",
            )
        ],
        avoid_or_short_watch=[],
        questions_for_user=["Is AI exposure too concentrated?"],
        cost=CostMetadata.zero(),
        prompt_hash="hash-model-a",
    )


def _context() -> DailyReportContext:
    return DailyReportContext(
        report_date="2026-05-31",
        market_context={
            "sp500_return_1d": 0.004,
            "nasdaq_return_1d": 0.007,
            "vix_level": 14.8,
        },
        sector_radar=["Semiconductors remain strong."],
        synthesis=synthesize_reports([_report()]),
        quant_signals=["NVDA quant score: 0.72"],
        paper_portfolio_actions=["Paper buy candidate: NVDA"],
        prediction_review=["No matured predictions today."],
    )


def test_renderer_outputs_required_markdown_sections() -> None:
    markdown = DailyReportRenderer().render_markdown(_context())

    for section in [
        "Market Regime",
        "Sector Radar",
        "Model Consensus",
        "Model Disagreements",
        "Ticker Theses",
        "Quant Signals",
        "Paper Portfolio Actions",
        "Prediction Review",
        "Questions For You",
    ]:
        assert f"## {section}" in markdown

    assert "NVDA" in markdown
    assert "AI infrastructure demand supports momentum." in markdown


def test_renderer_outputs_html_report() -> None:
    html = DailyReportRenderer().render_html(_context())

    assert "<!doctype html>" in html
    assert "<h1>Daily Research Report - 2026-05-31</h1>" in html
    assert "Model Consensus" in html
    assert "NVDA" in html


def test_renderer_archives_markdown_html_and_model_outputs(tmp_path) -> None:
    store = FileObjectStore(tmp_path)
    context = _context()

    keys = DailyReportRenderer().archive(store, context, model_outputs=[_report()])

    assert keys == {
        "markdown": "reports/2026/05/31/daily-report.md",
        "html": "reports/2026/05/31/daily-report.html",
        "model_outputs": "reports/2026/05/31/model-outputs.json",
    }
    assert store.exists(keys["markdown"])
    assert store.exists(keys["html"])
    assert store.exists(keys["model_outputs"])
    assert store.get_json(keys["model_outputs"])["model_outputs"][0]["model_id"] == "model/a"
