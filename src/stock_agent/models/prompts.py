from __future__ import annotations

import hashlib
import json
from typing import Any


SYSTEM_INSTRUCTIONS = """You are an independent equity research analyst.
Use only the supplied evidence pack.
Return a JSON analyst report matching the required schema.
Do not mention other models or prior model outputs."""


def build_analyst_prompt(evidence_pack: dict[str, Any]) -> str:
    evidence_json = json.dumps(evidence_pack, ensure_ascii=False, sort_keys=True)
    return f"{SYSTEM_INSTRUCTIONS}\n\nEvidence pack:\n{evidence_json}"


def prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()
