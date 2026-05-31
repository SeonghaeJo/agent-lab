from __future__ import annotations

import pytest

from stock_agent.storage.object_store import FileObjectStore


def test_file_object_store_round_trips_json(tmp_path) -> None:
    store = FileObjectStore(tmp_path)
    key = "reports/2026/05/31/model-outputs.json"
    payload = {"report_date": "2026-05-31", "models": ["openai/example"]}

    store.put_json(key, payload)

    assert store.exists(key)
    assert store.get_json(key) == payload


def test_file_object_store_writes_text(tmp_path) -> None:
    store = FileObjectStore(tmp_path)
    key = "reports/2026/05/31/daily-report.md"

    store.put_text(key, "# Daily Report\n")

    assert store.exists(key)
    assert (tmp_path / key).read_text() == "# Daily Report\n"


def test_file_object_store_rejects_path_traversal(tmp_path) -> None:
    store = FileObjectStore(tmp_path)

    with pytest.raises(ValueError, match="object key"):
        store.put_text("../outside.txt", "nope")
