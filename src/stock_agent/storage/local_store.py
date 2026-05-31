from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from stock_agent.storage.schemas import ModelOutput, RawDocument


class LocalStore:
    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS raw_documents (
                    source TEXT NOT NULL,
                    external_id TEXT NOT NULL,
                    url TEXT NOT NULL,
                    published_at TEXT NOT NULL,
                    fetched_at TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    object_key TEXT,
                    PRIMARY KEY (source, external_id)
                );

                CREATE INDEX IF NOT EXISTS idx_raw_documents_content_hash
                    ON raw_documents(content_hash);

                CREATE TABLE IF NOT EXISTS model_outputs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_date TEXT NOT NULL,
                    model_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    output_json TEXT NOT NULL,
                    prompt_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_model_outputs_report_date
                    ON model_outputs(report_date);
                """
            )

    def upsert_raw_document(self, document: RawDocument) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO raw_documents (
                    source,
                    external_id,
                    url,
                    published_at,
                    fetched_at,
                    content_hash,
                    object_key
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source, external_id) DO UPDATE SET
                    url = excluded.url,
                    published_at = excluded.published_at,
                    fetched_at = excluded.fetched_at,
                    content_hash = excluded.content_hash,
                    object_key = excluded.object_key
                """,
                (
                    document.source,
                    document.external_id,
                    document.url,
                    document.published_at,
                    document.fetched_at,
                    document.content_hash,
                    document.object_key,
                ),
            )

    def get_raw_document(self, source: str, external_id: str) -> RawDocument | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT source, external_id, url, published_at, fetched_at, content_hash, object_key
                FROM raw_documents
                WHERE source = ? AND external_id = ?
                """,
                (source, external_id),
            ).fetchone()
        return None if row is None else _raw_document_from_row(row)

    def list_raw_documents_by_hash(self, content_hash: str) -> list[RawDocument]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT source, external_id, url, published_at, fetched_at, content_hash, object_key
                FROM raw_documents
                WHERE content_hash = ?
                ORDER BY source, external_id
                """,
                (content_hash,),
            ).fetchall()
        return [_raw_document_from_row(row) for row in rows]

    def count_raw_documents(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM raw_documents").fetchone()
        return int(row["count"])

    def insert_model_output(self, output: ModelOutput) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO model_outputs (report_date, model_id, role, output_json, prompt_hash)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    output.report_date,
                    output.model_id,
                    output.role,
                    json.dumps(output.output_json, sort_keys=True),
                    output.prompt_hash,
                ),
            )

    def list_model_outputs(self, report_date: str) -> list[ModelOutput]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT report_date, model_id, role, output_json, prompt_hash
                FROM model_outputs
                WHERE report_date = ?
                ORDER BY id
                """,
                (report_date,),
            ).fetchall()
        return [_model_output_from_row(row) for row in rows]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection


def _raw_document_from_row(row: sqlite3.Row) -> RawDocument:
    return RawDocument(
        source=row["source"],
        external_id=row["external_id"],
        url=row["url"],
        published_at=row["published_at"],
        fetched_at=row["fetched_at"],
        content_hash=row["content_hash"],
        object_key=row["object_key"],
    )


def _model_output_from_row(row: sqlite3.Row) -> ModelOutput:
    return ModelOutput(
        report_date=row["report_date"],
        model_id=row["model_id"],
        role=row["role"],
        output_json=json.loads(row["output_json"]),
        prompt_hash=row["prompt_hash"],
    )
