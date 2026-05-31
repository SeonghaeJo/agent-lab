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
