from __future__ import annotations

import html
from dataclasses import asdict, dataclass
from typing import Any

from stock_agent.models.base import AnalystReport
from stock_agent.reports.synthesizer import SynthesisResult
from stock_agent.storage.object_store import FileObjectStore


@dataclass(frozen=True)
class DailyReportContext:
    report_date: str
    market_context: dict[str, Any]
    sector_radar: list[str]
    synthesis: SynthesisResult
    quant_signals: list[str]
    paper_portfolio_actions: list[str]
    prediction_review: list[str]


class DailyReportRenderer:
    def render_markdown(self, context: DailyReportContext) -> str:
        lines = [
            f"# Daily Research Report - {context.report_date}",
            "",
            "## Market Regime",
            *_bullet_lines(_market_context_lines(context.market_context)),
            "",
            "## Sector Radar",
            *_bullet_lines(context.sector_radar),
            "",
            "## Model Consensus",
            *_bullet_lines(_consensus_lines(context.synthesis)),
            "",
            "## Model Disagreements",
            *_bullet_lines(_disagreement_lines(context.synthesis)),
            "",
            "## Ticker Theses",
            *_bullet_lines(_ticker_thesis_lines(context.synthesis)),
            "",
            "## Quant Signals",
            *_bullet_lines(context.quant_signals),
            "",
            "## Paper Portfolio Actions",
            *_bullet_lines(context.paper_portfolio_actions),
            "",
            "## Prediction Review",
            *_bullet_lines(context.prediction_review),
            "",
            "## Questions For You",
            *_bullet_lines(context.synthesis.questions_for_user),
            "",
        ]
        return "\n".join(lines)

    def render_html(self, context: DailyReportContext) -> str:
        sections = [
            ("Market Regime", _market_context_lines(context.market_context)),
            ("Sector Radar", context.sector_radar),
            ("Model Consensus", _consensus_lines(context.synthesis)),
            ("Model Disagreements", _disagreement_lines(context.synthesis)),
            ("Ticker Theses", _ticker_thesis_lines(context.synthesis)),
            ("Quant Signals", context.quant_signals),
            ("Paper Portfolio Actions", context.paper_portfolio_actions),
            ("Prediction Review", context.prediction_review),
            ("Questions For You", context.synthesis.questions_for_user),
        ]
        section_html = "\n".join(
            f"<section><h2>{html.escape(title)}</h2>{_html_list(items)}</section>"
            for title, items in sections
        )
        return "\n".join(
            [
                "<!doctype html>",
                '<html lang="en">',
                "<head>",
                '  <meta charset="utf-8">',
                '  <meta name="viewport" content="width=device-width, initial-scale=1">',
                f"  <title>Daily Research Report - {html.escape(context.report_date)}</title>",
                "  <style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.55;max-width:960px;margin:32px auto;padding:0 18px;color:#172033}section{border-top:1px solid #d9e0ea;padding:18px 0}li{margin:8px 0}</style>",
                "</head>",
                "<body>",
                f"<h1>Daily Research Report - {html.escape(context.report_date)}</h1>",
                section_html,
                "</body>",
                "</html>",
            ]
        )

    def archive(
        self,
        store: FileObjectStore,
        context: DailyReportContext,
        *,
        model_outputs: list[AnalystReport],
    ) -> dict[str, str]:
        year, month, day = context.report_date.split("-")
        prefix = f"reports/{year}/{month}/{day}"
        keys = {
            "markdown": f"{prefix}/daily-report.md",
            "html": f"{prefix}/daily-report.html",
            "model_outputs": f"{prefix}/model-outputs.json",
        }
        store.put_text(keys["markdown"], self.render_markdown(context))
        store.put_text(keys["html"], self.render_html(context))
        store.put_json(
            keys["model_outputs"],
            {"model_outputs": [_report_to_json(report) for report in model_outputs]},
        )
        return keys


def _market_context_lines(market_context: dict[str, Any]) -> list[str]:
    if not market_context:
        return ["No market context available."]
    return [f"{key}: {value}" for key, value in sorted(market_context.items())]


def _consensus_lines(synthesis: SynthesisResult) -> list[str]:
    if not synthesis.consensus:
        return ["No model consensus today."]
    return [
        (
            f"{item.ticker} {item.direction} over {item.horizon_days}d "
            f"(avg p={item.average_probability}, models={', '.join(item.models)}; "
            f"catalysts={', '.join(item.catalysts) or 'none'}; risks={', '.join(item.risks) or 'none'})"
        )
        for item in synthesis.consensus
    ]


def _disagreement_lines(synthesis: SynthesisResult) -> list[str]:
    if not synthesis.disagreements:
        return ["No material model disagreements today."]
    lines: list[str] = []
    for item in synthesis.disagreements:
        model_views = ", ".join(
            f"{model}: {direction}"
            for model, direction in item.directions_by_model.items()
        )
        lines.append(f"{item.ticker} over {item.horizon_days}d: {model_views}")
    return lines


def _ticker_thesis_lines(synthesis: SynthesisResult) -> list[str]:
    if not synthesis.ticker_theses:
        return ["No ticker theses generated."]
    return [
        (
            f"{item.ticker} [{item.model_id}] {item.direction} p={item.probability}: "
            f"{item.thesis} Bear case: {item.bear_case}"
        )
        for item in synthesis.ticker_theses
    ]


def _bullet_lines(items: list[str]) -> list[str]:
    if not items:
        return ["- None."]
    return [f"- {item}" for item in items]


def _html_list(items: list[str]) -> str:
    if not items:
        return "<ul><li>None.</li></ul>"
    escaped = "".join(f"<li>{html.escape(item)}</li>" for item in items)
    return f"<ul>{escaped}</ul>"


def _report_to_json(report: AnalystReport) -> dict[str, Any]:
    return asdict(report)
