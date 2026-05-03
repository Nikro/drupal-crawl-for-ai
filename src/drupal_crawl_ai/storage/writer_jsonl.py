"""Append-safe JSONL writer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsonlWriter:
    """
    Append-safe newline-delimited JSON writer.

    Each ``write`` call appends one JSON line.
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, record: dict[str, Any]) -> None:
        """Append a single record as one JSON line."""
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")

    def write_batch(self, records: list[dict[str, Any]]) -> None:
        """Append multiple records as separate JSON lines."""
        with open(self._path, "a", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")
