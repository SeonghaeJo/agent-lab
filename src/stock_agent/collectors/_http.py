from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from typing import Any
from urllib.request import Request, urlopen


JsonHttpGet = Callable[[str, dict[str, str]], dict[str, Any]]


def get_json(url: str, headers: Mapping[str, str] | None = None) -> dict[str, Any]:
    request = Request(url, headers=dict(headers or {}))
    with urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8")
    payload = json.loads(body)
    if not isinstance(payload, dict):
        raise ValueError("Expected JSON object response")
    return payload
