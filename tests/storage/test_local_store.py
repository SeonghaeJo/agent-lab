from __future__ import annotations

from stock_agent.storage.local_store import LocalStore
from stock_agent.storage.schemas import ModelOutput, RawDocument


def test_raw_document_upsert_is_idempotent_by_source_and_external_id(tmp_path) -> None:
    store = LocalStore(tmp_path / "agent.sqlite")
    store.initialize()

    first = RawDocument(
        source="sec",
        external_id="0000320193-26-000001",
        url="https://www.sec.gov/example/old",
        published_at="2026-05-31T21:00:00Z",
        fetched_at="2026-05-31T21:02:00Z",
        content_hash="hash-old",
        object_key="sec/old.json",
    )
    second = RawDocument(
        source="sec",
        external_id="0000320193-26-000001",
        url="https://www.sec.gov/example/new",
        published_at="2026-05-31T21:00:00Z",
        fetched_at="2026-05-31T21:05:00Z",
        content_hash="hash-new",
        object_key="sec/new.json",
    )

    store.upsert_raw_document(first)
    store.upsert_raw_document(second)

    stored = store.get_raw_document("sec", "0000320193-26-000001")
    assert stored == second
    assert store.count_raw_documents() == 1


def test_raw_documents_can_be_found_by_content_hash(tmp_path) -> None:
    store = LocalStore(tmp_path / "agent.sqlite")
    store.initialize()

    store.upsert_raw_document(
        RawDocument(
            source="gdelt",
            external_id="article-1",
            url="https://example.com/a",
            published_at="2026-05-31T13:20:00Z",
            fetched_at="2026-05-31T13:25:00Z",
            content_hash="same-story",
            object_key=None,
        )
    )
    store.upsert_raw_document(
        RawDocument(
            source="newsapi",
            external_id="article-2",
            url="https://mirror.example.com/a",
            published_at="2026-05-31T13:21:00Z",
            fetched_at="2026-05-31T13:26:00Z",
            content_hash="same-story",
            object_key=None,
        )
    )

    matches = store.list_raw_documents_by_hash("same-story")
    assert [document.source for document in matches] == ["gdelt", "newsapi"]


def test_model_outputs_can_be_queried_by_report_date(tmp_path) -> None:
    store = LocalStore(tmp_path / "agent.sqlite")
    store.initialize()

    store.insert_model_output(
        ModelOutput(
            report_date="2026-05-31",
            model_id="openai/example",
            role="fast_analyst",
            output_json={"market_view": "risk-on"},
            prompt_hash="prompt-1",
        )
    )
    store.insert_model_output(
        ModelOutput(
            report_date="2026-06-01",
            model_id="anthropic/example",
            role="reasoning_analyst",
            output_json={"market_view": "neutral"},
            prompt_hash="prompt-2",
        )
    )

    outputs = store.list_model_outputs("2026-05-31")
    assert len(outputs) == 1
    assert outputs[0].model_id == "openai/example"
    assert outputs[0].output_json == {"market_view": "risk-on"}
