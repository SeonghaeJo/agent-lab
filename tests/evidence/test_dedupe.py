from __future__ import annotations

from stock_agent.evidence.dedupe import (
    DocumentFingerprintInput,
    dedupe_by_fingerprint,
    fingerprint_document,
    normalize_text,
    normalize_url,
)


def test_normalize_url_removes_tracking_params_fragment_and_trailing_slash() -> None:
    assert (
        normalize_url(
            "HTTPS://Example.com/News/NVDA/?utm_source=feed&b=2&a=1#section"
        )
        == "https://example.com/News/NVDA?a=1&b=2"
    )


def test_fingerprint_document_uses_normalized_url_and_text() -> None:
    first = fingerprint_document(
        DocumentFingerprintInput(
            url="https://example.com/article?utm_medium=social",
            title="  Nvidia   suppliers rally ",
            body="AI infrastructure demand rises.",
        )
    )
    second = fingerprint_document(
        DocumentFingerprintInput(
            url="https://example.com/article",
            title="NVIDIA suppliers rally",
            body="ai infrastructure demand rises.",
        )
    )

    assert first == second


def test_normalize_text_compacts_whitespace_and_casefolds() -> None:
    assert normalize_text("  AI\tInfrastructure\nDemand  ") == "ai infrastructure demand"


def test_dedupe_by_fingerprint_keeps_first_unique_document() -> None:
    documents = [
        DocumentFingerprintInput(
            url="https://example.com/a?utm_campaign=x",
            title="Same story",
            body="Same body",
        ),
        DocumentFingerprintInput(
            url="https://example.com/a",
            title="same story",
            body="same body",
        ),
        DocumentFingerprintInput(
            url="https://example.com/b",
            title="Different story",
            body="Different body",
        ),
    ]

    unique = dedupe_by_fingerprint(documents)

    assert unique == [documents[0], documents[2]]
