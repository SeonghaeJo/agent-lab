from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RawDocument:
    source: str
    external_id: str
    url: str
    published_at: str
    fetched_at: str
    content_hash: str
    object_key: str | None


@dataclass(frozen=True)
class ModelOutput:
    report_date: str
    model_id: str
    role: str
    output_json: dict[str, Any]
    prompt_hash: str


@dataclass(frozen=True)
class TickerPrice:
    ticker: str
    trading_date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    provider: str


@dataclass(frozen=True)
class Prediction:
    prediction_id: str
    report_date: str
    ticker: str
    horizon_days: int
    direction: str
    probability: float
    evidence_ids: list[str]
    model_id: str


@dataclass(frozen=True)
class PaperTrade:
    order_id: str
    submitted_at: str
    ticker: str
    side: str
    qty: float
    limit_price: float | None
    status: str
    provider: str


@dataclass(frozen=True)
class EvaluationScore:
    prediction_id: str
    evaluated_at: str
    realized_return: float
    benchmark_return: float
    excess_return: float
    score_json: dict[str, Any]
