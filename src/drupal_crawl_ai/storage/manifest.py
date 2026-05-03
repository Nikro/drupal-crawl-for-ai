"""Run manifest and checkpoint reader/writer with atomic writes."""

from __future__ import annotations

import json
import uuid
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

from drupal_crawl_ai.config import Config, OutputConfig


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RunManifest(Mapping):
    """
    Run manifest and checkpoint tracker.

    Implements the run manifest schema with atomic writes (temp file + rename).
    """

    def __init__(
        self,
        run_id: str | None = None,
        config: Config | None = None,
        output_config: OutputConfig | None = None,
    ) -> None:
        self._config = config or Config()
        self._output = output_config or self._config.output
        self._run_id = run_id or str(uuid.uuid4())[:8]
        self._path = self._output.runs_dir() / self._run_id / "manifest.json"
        self._data: dict[str, Any] = {}

    @property
    def run_id(self) -> str:
        return self._run_id

    @property
    def path(self) -> Path:
        return self._path

    def _ensure_dir(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)

    # --- Mapping interface (read-only dict-like access) ---

    def __getitem__(self, key: str) -> Any:
        if not self._data:
            self._data = self._load_data()
        return self._data[key]

    def __iter__(self) -> Any:
        if not self._data:
            self._data = self._load_data()
        return iter(self._data)

    def __len__(self) -> int:
        if not self._data:
            self._data = self._load_data()
        return len(self._data)

    def _load_data(self) -> dict[str, Any]:
        if self._path.exists():
            with open(self._path, encoding="utf-8") as f:
                return cast(dict[str, Any], json.load(f))
        return self._new_manifest()

    # --- Write operations ---

    def _new_manifest(self) -> dict[str, Any]:
        return {
            "run_id": self._run_id,
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
            "status": "running",
            "options": {},
            "cursor": {},
            "counters": {
                "fetched": 0,
                "succeeded": 0,
                "failed": 0,
                "skipped_duplicates": 0,
                "cache_hits": 0,
            },
            "failures": [],
            "source_modes": {},
        }

    def write_initial(self, command: str, options: dict[str, Any]) -> None:
        self._ensure_dir()
        self._data = self._new_manifest()
        self._data["command"] = command
        self._data["options"] = options
        self._persist()

    def _reload(self) -> None:
        self._data = self._load_data()

    def update_cursor(self, cursor: dict[str, Any]) -> None:
        self._data["cursor"] = cursor
        self._data["updated_at"] = _now_iso()
        self._persist()

    def increment(self, key: str, value: int = 1) -> None:
        if key in self._data["counters"]:
            self._data["counters"][key] += value
        self._data["updated_at"] = _now_iso()
        self._persist()

    def record_failure(
        self,
        url: str,
        status_code: int,
        error: str,
        entity_id: int | str | None = None,
    ) -> None:
        self._data["failures"].append({
            "url": url,
            "status_code": status_code,
            "error": error,
            "entity_id": entity_id,
        })
        self._data["counters"]["failed"] += 1
        self._data["updated_at"] = _now_iso()
        self._persist()

    def record_source_mode(self, mode: str) -> None:
        counts = self._data.setdefault("source_modes", {})
        counts[mode] = counts.get(mode, 0) + 1
        self._data["updated_at"] = _now_iso()
        self._persist()

    def mark_completed(self) -> None:
        self._data["status"] = "completed"
        self._data["updated_at"] = _now_iso()
        self._persist()

    def mark_failed(self, error: str) -> None:
        self._data["status"] = "failed"
        self._data["updated_at"] = _now_iso()
        self._data["failures"].append({"error": error})
        self._persist()

    def _persist(self) -> None:
        """Atomic write: temp file + rename."""
        self._ensure_dir()
        tmp = self._path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)
        tmp.rename(self._path)

    # --- Read operations ---

    @classmethod
    def load(cls, run_id: str, config: Config | None = None) -> RunManifest:
        """Load existing manifest from a run_id directory."""
        manifest = cls(run_id=run_id, config=config)
        if not manifest._path.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest._path}")
        manifest._data = manifest._load_data()
        return manifest

    @property
    def status(self) -> str:
        return self._data.get("status", "unknown")  # type: ignore[no-any-return]

    @property
    def cursor(self) -> dict[str, Any]:
        return self._data.get("cursor", {})  # type: ignore[no-any-return]

    @property
    def counters(self) -> dict[str, int]:
        return self._data.get("counters", {})  # type: ignore[no-any-return]

    @property
    def is_resumable(self) -> bool:
        return self._data.get("status") == "running"
