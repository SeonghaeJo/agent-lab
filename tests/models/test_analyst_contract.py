from __future__ import annotations

import copy

import pytest

from stock_agent.models.base import (
    AnalystValidationError,
    BudgetExceededError,
    CandidatePrediction,
    CostMetadata,
    StaticModelAdapter,
    validate_analyst_report,
)
from stock_agent.models.openai_adapter import OpenAIAdapter
from stock_agent.models.anthropic_adapter import AnthropicAdapter
from stock_agent.models.gemini_adapter import GeminiAdapter
from stock_agent.models.prompts import build_analyst_prompt, prompt_hash
from stock_agent.reports.analyst_runner import AnalystRunner


VALID_REPORT = {
    "model_id": "provider/model",
    "report_date": "2026-05-31",
    "analyst_role": "fast_analyst",
    "market_view": "risk-on",
    "top_long_candidates": [
        {
            "ticker": "NVDA",
            "horizon_days": 5,
            "direction": "up",
            "probability": 0.62,
            "confidence": "medium",
            "thesis": "AI infrastructure demand supports near-term momentum.",
            "bull_case": "Demand commentary and price momentum align.",
            "bear_case": "Valuation can reverse sentiment quickly.",
            "catalysts": ["sector momentum"],
            "risks": ["valuation"],
            "evidence_ids": ["news_1", "sec_1"],
            "review_after": "2026-06-07",
        }
    ],
    "avoid_or_short_watch": [],
    "questions_for_user": ["Is the portfolio too concentrated in AI infrastructure?"],
}


def test_validate_analyst_report_returns_typed_report_with_cost_and_prompt_metadata() -> None:
    report = validate_analyst_report(
        VALID_REPORT,
        cost=CostMetadata(
            input_tokens=100,
            output_tokens=50,
            estimated_cost_usd=0.01,
            raw_response_location="objects/raw/openai.json",
        ),
        prompt_hash="abc123",
    )

    assert report.model_id == "provider/model"
    assert report.cost.estimated_cost_usd == 0.01
    assert report.raw_response_location == "objects/raw/openai.json"
    assert report.prompt_hash == "abc123"
    assert report.top_long_candidates == [
        CandidatePrediction(
            ticker="NVDA",
            horizon_days=5,
            direction="up",
            probability=0.62,
            confidence="medium",
            thesis="AI infrastructure demand supports near-term momentum.",
            bull_case="Demand commentary and price momentum align.",
            bear_case="Valuation can reverse sentiment quickly.",
            catalysts=["sector momentum"],
            risks=["valuation"],
            evidence_ids=["news_1", "sec_1"],
            review_after="2026-06-07",
        )
    ]


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("ticker", "ticker"),
        ("horizon_days", "horizon_days"),
        ("direction", "direction"),
        ("probability", "probability"),
        ("thesis", "thesis"),
        ("bear_case", "bear_case"),
        ("risks", "risks"),
        ("evidence_ids", "evidence_ids"),
    ],
)
def test_validate_analyst_report_rejects_missing_required_candidate_fields(
    field: str,
    message: str,
) -> None:
    payload = {
        **VALID_REPORT,
        "top_long_candidates": [
            {
                key: value
                for key, value in VALID_REPORT["top_long_candidates"][0].items()
                if key != field
            }
        ],
    }

    with pytest.raises(AnalystValidationError, match=message):
        validate_analyst_report(payload, cost=CostMetadata.zero(), prompt_hash="abc123")


def test_validate_analyst_report_rejects_invalid_probability_and_direction() -> None:
    invalid_probability = {
        **VALID_REPORT,
        "top_long_candidates": [
            {
                **VALID_REPORT["top_long_candidates"][0],
                "probability": 1.7,
            }
        ],
    }
    with pytest.raises(AnalystValidationError, match="probability"):
        validate_analyst_report(
            invalid_probability,
            cost=CostMetadata.zero(),
            prompt_hash="abc123",
        )

    invalid_direction = {
        **VALID_REPORT,
        "top_long_candidates": [
            {
                **VALID_REPORT["top_long_candidates"][0],
                "direction": "sideways",
            }
        ],
    }
    with pytest.raises(AnalystValidationError, match="direction"):
        validate_analyst_report(
            invalid_direction,
            cost=CostMetadata.zero(),
            prompt_hash="abc123",
        )


def test_prompt_hash_is_stable_for_same_prompt() -> None:
    prompt = build_analyst_prompt({"report_date": "2026-05-31", "ticker_evidence": []})

    assert prompt_hash(prompt) == prompt_hash(prompt)
    assert len(prompt_hash(prompt)) == 64


def test_provider_adapters_build_expected_provider_model_ids() -> None:
    assert OpenAIAdapter(model="gpt-test").model_id == "openai/gpt-test"
    assert AnthropicAdapter(model="claude-test").model_id == "anthropic/claude-test"
    assert GeminiAdapter(model="gemini-test").model_id == "gemini/gemini-test"


def test_runner_sends_same_evidence_pack_to_each_model_independently() -> None:
    seen_inputs: list[tuple[str, dict]] = []
    evidence_pack = {
        "report_date": "2026-05-31",
        "ticker_evidence": [{"ticker": "NVDA"}],
    }

    def make_adapter(model_id: str) -> StaticModelAdapter:
        payload = {**VALID_REPORT, "model_id": model_id}

        def response_factory(received_pack: dict) -> dict:
            seen_inputs.append((model_id, copy.deepcopy(received_pack)))
            received_pack["mutated_by"] = model_id
            return payload

        return StaticModelAdapter(
            model_id=model_id,
            analyst_role="fast_analyst",
            response_factory=response_factory,
            estimated_cost_usd=0.01,
        )

    runner = AnalystRunner(daily_budget_usd=0.10)

    reports = runner.run(
        evidence_pack=evidence_pack,
        adapters=[make_adapter("model/a"), make_adapter("model/b")],
    )

    assert [report.model_id for report in reports] == ["model/a", "model/b"]
    assert seen_inputs == [
        ("model/a", {"report_date": "2026-05-31", "ticker_evidence": [{"ticker": "NVDA"}]}),
        ("model/b", {"report_date": "2026-05-31", "ticker_evidence": [{"ticker": "NVDA"}]}),
    ]
    assert "mutated_by" not in evidence_pack


def test_runner_enforces_input_size_output_token_and_daily_spend_budget() -> None:
    runner = AnalystRunner(
        daily_budget_usd=0.01,
        max_input_chars=20,
        max_output_tokens=100,
    )

    with pytest.raises(BudgetExceededError, match="input size"):
        runner.run(
            evidence_pack={"long": "x" * 100},
            adapters=[],
        )

    output_budget_runner = AnalystRunner(
        daily_budget_usd=1.00,
        max_input_chars=1_000,
        max_output_tokens=100,
    )
    with pytest.raises(BudgetExceededError, match="output tokens"):
        output_budget_runner.run(
            evidence_pack={"short": "ok"},
            adapters=[
                StaticModelAdapter(
                    model_id="model/too-large",
                    analyst_role="fast_analyst",
                    response_factory=lambda _: VALID_REPORT,
                    max_output_tokens=500,
                )
            ],
        )

    spend_budget_runner = AnalystRunner(
        daily_budget_usd=0.01,
        max_input_chars=1_000,
        max_output_tokens=100,
    )
    with pytest.raises(BudgetExceededError, match="daily spend"):
        spend_budget_runner.run(
            evidence_pack={"short": "ok"},
            adapters=[
                StaticModelAdapter(
                    model_id="model/too-expensive",
                    analyst_role="fast_analyst",
                    response_factory=lambda _: VALID_REPORT,
                    estimated_cost_usd=0.02,
                )
            ],
        )
