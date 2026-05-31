from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class FileObjectStore:
    """Filesystem-backed archive with the same key shape as object storage."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def put_json(self, key: str, payload: dict[str, Any]) -> None:
        path = self._path_for_key(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def get_json(self, key: str) -> dict[str, Any]:
        path = self._path_for_key(key)
        return json.loads(path.read_text(encoding="utf-8"))

    def put_text(self, key: str, text: str) -> None:
        path = self._path_for_key(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def exists(self, key: str) -> bool:
        return self._path_for_key(key).exists()

    def _path_for_key(self, key: str) -> Path:
        parts = Path(key).parts
        if not key or Path(key).is_absolute() or ".." in parts:
            raise ValueError(f"Invalid object key: {key}")

        path = (self.root / key).resolve()
        try:
            path.relative_to(self.root)
        except ValueError as exc:
            raise ValueError(f"Invalid object key: {key}") from exc
        return path
