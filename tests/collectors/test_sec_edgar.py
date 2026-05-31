from __future__ import annotations

from stock_agent.collectors.sec_edgar import SecEdgarClient


def test_sec_edgar_fetches_recent_filings_with_polite_user_agent() -> None:
    calls: list[tuple[str, dict[str, str]]] = []

    def fake_get(url: str, headers: dict[str, str]) -> dict:
        calls.append((url, headers))
        return {
            "filings": {
                "recent": {
                    "accessionNumber": [
                        "0000320193-26-000001",
                        "0000320193-26-000002",
                    ],
                    "form": ["8-K", "4"],
                    "filingDate": ["2026-05-31", "2026-05-30"],
                    "primaryDocument": ["aapl-20260531.htm", "ownership.xml"],
                }
            }
        }

    client = SecEdgarClient(
        user_agent="stock-research-agent test@example.com",
        http_get=fake_get,
    )

    filings = client.list_recent_filings("320193", forms={"8-K"})

    assert calls == [
        (
            "https://data.sec.gov/submissions/CIK0000320193.json",
            {"User-Agent": "stock-research-agent test@example.com"},
        )
    ]
    assert len(filings) == 1
    assert filings[0].accession_number == "0000320193-26-000001"
    assert filings[0].form == "8-K"
    assert filings[0].filed_at == "2026-05-31"
    assert filings[0].primary_document == "aapl-20260531.htm"
    assert client.last_request_at is not None
