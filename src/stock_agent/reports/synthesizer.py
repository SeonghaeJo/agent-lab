from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from stock_agent.models.base import AnalystReport, CandidatePrediction


@dataclass(frozen=True)
class ConsensusItem:
    ticker: str
    horizon_days: int
    direction: str
    models: list[str]
    average_probability: float
    catalysts: list[str]
    risks: list[str]


@dataclass(frozen=True)
class DisagreementItem:
    ticker: str
    horizon_days: int
    directions_by_model: dict[str, str]
    probabilities_by_model: dict[str, float]
    theses_by_model: dict[str, str]


@dataclass(frozen=True)
class TickerThesis:
    ticker: str
    model_id: str
    horizon_days: int
    direction: str
    probability: float
    thesis: str
    bear_case: str
    risks: list[str]
    evidence_ids: list[str]


@dataclass(frozen=True)
class SynthesisResult:
    report_date: str
    model_ids: list[str]
    consensus: list[ConsensusItem]
    disagreements: list[DisagreementItem]
    ticker_theses: list[TickerThesis]
    questions_for_user: list[str]


def synthesize_reports(reports: list[AnalystReport]) -> SynthesisResult:
    if not reports:
        return SynthesisResult(
            report_date="",
            model_ids=[],
            consensus=[],
            disagreements=[],
            ticker_theses=[],
            questions_for_user=[],
        )

    grouped: dict[tuple[str, int], list[tuple[str, CandidatePrediction]]] = defaultdict(list)
    ticker_theses: list[TickerThesis] = []
    questions: list[str] = []

    for report in reports:
        questions.extend(report.questions_for_user)
        for candidate in report.top_long_candidates:
            grouped[(candidate.ticker, candidate.horizon_days)].append(
                (report.model_id, candidate)
            )
            ticker_theses.append(
                TickerThesis(
                    ticker=candidate.ticker,
                    model_id=report.model_id,
                    horizon_days=candidate.horizon_days,
                    direction=candidate.direction,
                    probability=candidate.probability,
                    thesis=candidate.thesis,
                    bear_case=candidate.bear_case,
                    risks=candidate.risks,
                    evidence_ids=candidate.evidence_ids,
                )
            )

    consensus: list[ConsensusItem] = []
    disagreements: list[DisagreementItem] = []
    for (ticker, horizon_days), items in grouped.items():
        directions = {candidate.direction for _, candidate in items}
        if len(items) > 1 and len(directions) == 1:
            consensus.append(_build_consensus_item(ticker, horizon_days, items))
        elif len(directions) > 1:
            disagreements.append(_build_disagreement_item(ticker, horizon_days, items))

    return SynthesisResult(
        report_date=reports[0].report_date,
        model_ids=[report.model_id for report in reports],
        consensus=sorted(consensus, key=lambda item: (-len(item.models), item.ticker)),
        disagreements=sorted(disagreements, key=lambda item: item.ticker),
        ticker_theses=sorted(ticker_theses, key=lambda item: (item.ticker, item.model_id)),
        questions_for_user=_unique_sorted_by_first_seen(questions),
    )


def _build_consensus_item(
    ticker: str,
    horizon_days: int,
    items: list[tuple[str, CandidatePrediction]],
) -> ConsensusItem:
    probabilities = [candidate.probability for _, candidate in items]
    return ConsensusItem(
        ticker=ticker,
        horizon_days=horizon_days,
        direction=items[0][1].direction,
        models=[model_id for model_id, _ in items],
        average_probability=round(sum(probabilities) / len(probabilities), 2),
        catalysts=_unique_sorted(
            catalyst for _, candidate in items for catalyst in candidate.catalysts
        ),
        risks=_unique_sorted(risk for _, candidate in items for risk in candidate.risks),
    )


def _build_disagreement_item(
    ticker: str,
    horizon_days: int,
    items: list[tuple[str, CandidatePrediction]],
) -> DisagreementItem:
    return DisagreementItem(
        ticker=ticker,
        horizon_days=horizon_days,
        directions_by_model={model_id: candidate.direction for model_id, candidate in items},
        probabilities_by_model={
            model_id: candidate.probability for model_id, candidate in items
        },
        theses_by_model={model_id: candidate.thesis for model_id, candidate in items},
    )


def _unique_sorted(values) -> list[str]:
    return sorted(set(values))


def _unique_sorted_by_first_seen(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
