from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol


class AnalystValidationError(ValueError):
    """Raised when a model response does not satisfy the analyst contract."""


class BudgetExceededError(ValueError):
    """Raised before a model run that would exceed configured budgets."""


@dataclass(frozen=True)
class CostMetadata:
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    raw_response_location: str | None = None

    @classmethod
    def zero(cls) -> CostMetadata:
        return cls(input_tokens=0, output_tokens=0, estimated_cost_usd=0.0)


@dataclass(frozen=True)
class CandidatePrediction:
    ticker: str
    horizon_days: int
    direction: str
    probability: float
    confidence: str
    thesis: str
    bull_case: str
    bear_case: str
    catalysts: list[str]
    risks: list[str]
    evidence_ids: list[str]
    review_after: str


@dataclass(frozen=True)
class AnalystReport:
    model_id: str
    report_date: str
    analyst_role: str
    market_view: str
    top_long_candidates: list[CandidatePrediction]
    avoid_or_short_watch: list[CandidatePrediction]
    questions_for_user: list[str]
    cost: CostMetadata
    prompt_hash: str
    raw_response_location: str | None = None


class ModelAdapter(Protocol):
    model_id: str
    analyst_role: str
    max_output_tokens: int
    estimated_cost_usd: float

    def generate(self, evidence_pack: dict[str, Any], prompt: str) -> dict[str, Any]:
        """Return a provider-normalized analyst report JSON object."""


@dataclass
class StaticModelAdapter:
    model_id: str
    analyst_role: str
    response_factory: Callable[[dict[str, Any]], dict[str, Any]]
    estimated_cost_usd: float = 0.0
    max_output_tokens: int = 100

    def generate(self, evidence_pack: dict[str, Any], prompt: str) -> dict[str, Any]:
        return self.response_factory(copy.deepcopy(evidence_pack))


def validate_analyst_report(
    payload: dict[str, Any],
    *,
    cost: CostMetadata,
    prompt_hash: str,
) -> AnalystReport:
    model_id = _required_str(payload, "model_id")
    report_date = _required_str(payload, "report_date")
    analyst_role = _required_str(payload, "analyst_role")
    market_view = _required_str(payload, "market_view")

    top_long_candidates = _candidate_list(payload, "top_long_candidates")
    avoid_or_short_watch = _candidate_list(payload, "avoid_or_short_watch")
    questions_for_user = _string_list(payload, "questions_for_user")

    return AnalystReport(
        model_id=model_id,
        report_date=report_date,
        analyst_role=analyst_role,
        market_view=market_view,
        top_long_candidates=top_long_candidates,
        avoid_or_short_watch=avoid_or_short_watch,
        questions_for_user=questions_for_user,
        cost=cost,
        prompt_hash=prompt_hash,
        raw_response_location=cost.raw_response_location,
    )


def _candidate_list(payload: dict[str, Any], field_name: str) -> list[CandidatePrediction]:
    value = payload.get(field_name)
    if not isinstance(value, list):
        raise AnalystValidationError(f"{field_name} must be a list")
    return [_candidate_from_payload(item, f"{field_name}[{index}]") for index, item in enumerate(value)]


def _candidate_from_payload(payload: Any, path: str) -> CandidatePrediction:
    if not isinstance(payload, dict):
        raise AnalystValidationError(f"{path} must be an object")

    ticker = _required_str(payload, "ticker", path)
    horizon_days = _required_int(payload, "horizon_days", path)
    direction = _required_str(payload, "direction", path)
    if direction not in {"up", "down", "flat"}:
        raise AnalystValidationError(f"{path}.direction must be one of up, down, flat")

    probability = _required_float(payload, "probability", path)
    if probability < 0.0 or probability > 1.0:
        raise AnalystValidationError(f"{path}.probability must be between 0 and 1")

    return CandidatePrediction(
        ticker=ticker,
        horizon_days=horizon_days,
        direction=direction,
        probability=probability,
        confidence=_required_str(payload, "confidence", path),
        thesis=_required_str(payload, "thesis", path),
        bull_case=_required_str(payload, "bull_case", path),
        bear_case=_required_str(payload, "bear_case", path),
        catalysts=_string_list(payload, "catalysts", path),
        risks=_non_empty_string_list(payload, "risks", path),
        evidence_ids=_non_empty_string_list(payload, "evidence_ids", path),
        review_after=_required_str(payload, "review_after", path),
    )


def _required_str(payload: dict[str, Any], field_name: str, path: str = "report") -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise AnalystValidationError(f"{path}.{field_name} is required")
    return value


def _required_int(payload: dict[str, Any], field_name: str, path: str) -> int:
    value = payload.get(field_name)
    if not isinstance(value, int):
        raise AnalystValidationError(f"{path}.{field_name} is required")
    return value


def _required_float(payload: dict[str, Any], field_name: str, path: str) -> float:
    value = payload.get(field_name)
    if not isinstance(value, int | float):
        raise AnalystValidationError(f"{path}.{field_name} is required")
    return float(value)


def _string_list(
    payload: dict[str, Any],
    field_name: str,
    path: str = "report",
) -> list[str]:
    value = payload.get(field_name)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise AnalystValidationError(f"{path}.{field_name} must be a list of strings")
    return list(value)


def _non_empty_string_list(payload: dict[str, Any], field_name: str, path: str) -> list[str]:
    values = _string_list(payload, field_name, path)
    if not values:
        raise AnalystValidationError(f"{path}.{field_name} must not be empty")
    return values
