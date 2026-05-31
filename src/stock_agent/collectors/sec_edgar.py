from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from stock_agent.collectors._http import JsonHttpGet, get_json


@dataclass(frozen=True)
class SecFiling:
    accession_number: str
    form: str
    filed_at: str
    primary_document: str


class SecEdgarClient:
    submissions_base_url = "https://data.sec.gov/submissions"

    def __init__(
        self,
        user_agent: str,
        http_get: JsonHttpGet | None = None,
    ) -> None:
        if not user_agent.strip():
            raise ValueError("SEC EDGAR User-Agent must not be empty")
        self.user_agent = user_agent
        self.http_get = http_get or get_json
        self.last_request_at: str | None = None

    def list_recent_filings(
        self,
        cik: str,
        forms: set[str] | None = None,
    ) -> list[SecFiling]:
        payload = self.http_get(self._submissions_url(cik), {"User-Agent": self.user_agent})
        self.last_request_at = datetime.now(UTC).isoformat()

        recent = payload.get("filings", {}).get("recent", {})
        accession_numbers = recent.get("accessionNumber", [])
        form_names = recent.get("form", [])
        filing_dates = recent.get("filingDate", [])
        primary_documents = recent.get("primaryDocument", [])

        allowed_forms = {form.upper() for form in forms} if forms is not None else None
        filings: list[SecFiling] = []
        for accession_number, form, filed_at, primary_document in zip(
            accession_numbers,
            form_names,
            filing_dates,
            primary_documents,
            strict=False,
        ):
            if allowed_forms is not None and form.upper() not in allowed_forms:
                continue
            filings.append(
                SecFiling(
                    accession_number=accession_number,
                    form=form,
                    filed_at=filed_at,
                    primary_document=primary_document,
                )
            )
        return filings

    def _submissions_url(self, cik: str) -> str:
        normalized = "".join(character for character in cik if character.isdigit()).zfill(10)
        return f"{self.submissions_base_url}/CIK{normalized}.json"
