from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


TRACKING_PARAMS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "utm_campaign",
    "utm_content",
    "utm_medium",
    "utm_source",
    "utm_term",
}


@dataclass(frozen=True)
class DocumentFingerprintInput:
    url: str
    title: str
    body: str


def normalize_url(url: str) -> str:
    parsed = urlsplit(url.strip())
    query_pairs = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key.lower() not in TRACKING_PARAMS
    ]
    normalized_query = urlencode(sorted(query_pairs))
    normalized_path = parsed.path.rstrip("/") or parsed.path

    return urlunsplit(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            normalized_path,
            normalized_query,
            "",
        )
    )


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold()).strip()


def fingerprint_document(document: DocumentFingerprintInput) -> str:
    normalized = "\n".join(
        [
            normalize_url(document.url),
            normalize_text(document.title),
            normalize_text(document.body),
        ]
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def dedupe_by_fingerprint(
    documents: list[DocumentFingerprintInput],
) -> list[DocumentFingerprintInput]:
    seen: set[str] = set()
    unique: list[DocumentFingerprintInput] = []
    for document in documents:
        fingerprint = fingerprint_document(document)
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        unique.append(document)
    return unique
