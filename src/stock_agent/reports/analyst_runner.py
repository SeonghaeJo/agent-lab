from __future__ import annotations

import copy
import json
from typing import Any

from stock_agent.models.base import (
    AnalystReport,
    BudgetExceededError,
    CostMetadata,
    ModelAdapter,
    validate_analyst_report,
)
from stock_agent.models.prompts import build_analyst_prompt, prompt_hash


class AnalystRunner:
    def __init__(
        self,
        *,
        daily_budget_usd: float,
        max_input_chars: int = 40_000,
        max_output_tokens: int = 2_000,
    ) -> None:
        self.daily_budget_usd = daily_budget_usd
        self.max_input_chars = max_input_chars
        self.max_output_tokens = max_output_tokens

    def run(
        self,
        *,
        evidence_pack: dict[str, Any],
        adapters: list[ModelAdapter],
    ) -> list[AnalystReport]:
        prompt = build_analyst_prompt(evidence_pack)
        self._check_input_size(prompt)
        self._check_adapter_budgets(adapters)

        digest = prompt_hash(prompt)
        reports: list[AnalystReport] = []
        for adapter in adapters:
            response = adapter.generate(copy.deepcopy(evidence_pack), prompt)
            cost = CostMetadata(
                input_tokens=_rough_token_count(prompt),
                output_tokens=adapter.max_output_tokens,
                estimated_cost_usd=adapter.estimated_cost_usd,
            )
            reports.append(validate_analyst_report(response, cost=cost, prompt_hash=digest))
        return reports

    def _check_input_size(self, prompt: str) -> None:
        if len(prompt) > self.max_input_chars:
            raise BudgetExceededError(
                f"Prompt input size {len(prompt)} exceeds input size budget {self.max_input_chars}"
            )

    def _check_adapter_budgets(self, adapters: list[ModelAdapter]) -> None:
        for adapter in adapters:
            if adapter.max_output_tokens > self.max_output_tokens:
                raise BudgetExceededError(
                    f"{adapter.model_id} output tokens {adapter.max_output_tokens} "
                    f"exceed output tokens budget {self.max_output_tokens}"
                )

        estimated_total = sum(adapter.estimated_cost_usd for adapter in adapters)
        if estimated_total > self.daily_budget_usd:
            raise BudgetExceededError(
                f"Estimated daily spend {estimated_total:.4f} exceeds daily spend budget "
                f"{self.daily_budget_usd:.4f}"
            )


def _rough_token_count(text: str) -> int:
    return max(1, len(text) // 4)
