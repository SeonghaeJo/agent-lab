from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AnthropicAdapter:
    model: str
    analyst_role: str = "reasoning_analyst"
    max_output_tokens: int = 1200
    estimated_cost_usd: float = 0.0

    @property
    def model_id(self) -> str:
        return f"anthropic/{self.model}"

    def generate(self, evidence_pack: dict[str, Any], prompt: str) -> dict[str, Any]:
        raise NotImplementedError("Anthropic API calls will be implemented after the contract layer")
