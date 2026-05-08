"""Unit tests for RunManifest."""

from __future__ import annotations

from pathlib import Path

import pytest
from drupal_crawl_ai.config import Config
from drupal_crawl_ai.storage.manifest import RunManifest


def test_write_initial_creates_file(tmp_path: Path) -> None:
    cfg = Config()
    cfg.output._runs_root = tmp_path  # type: ignore[assignment]
    manifest = RunManifest(config=cfg)
    manifest.write_initial("changes --project 3060", {"projects": [3060]})
    assert manifest.path.exists()


def test_atomic_write(tmp_path: Path) -> None:
    cfg = Config()
    cfg.output._runs_root = tmp_path  # type: ignore[assignment]
    manifest = RunManifest(config=cfg)
    manifest.write_initial("issues --project 3060", {})
    # Verify .tmp is not present (renamed to final)
    tmp_files = list(tmp_path.rglob("*.tmp"))
    assert len(tmp_files) == 0


def test_update_cursor_persists_correctly(tmp_path: Path) -> None:
    cfg = Config()
    cfg.output._runs_root = tmp_path  # type: ignore[assignment]
    manifest = RunManifest(config=cfg)
    manifest.write_initial("issues --project 3060", {})
    manifest.update_cursor({"page": 2, "last_entity_id": 12345})
    # Reload
    reloaded = RunManifest.load(manifest.run_id, config=cfg)
    assert reloaded.cursor["page"] == 2
    assert reloaded.cursor["last_entity_id"] == 12345


def test_increment_counters(tmp_path: Path) -> None:
    cfg = Config()
    cfg.output._runs_root = tmp_path  # type: ignore[assignment]
    manifest = RunManifest(config=cfg)
    manifest.write_initial("issues --project 3060", {})
    manifest.increment("succeeded", 3)
    manifest.increment("cache_hits", 1)
    assert manifest.counters["succeeded"] == 3
    assert manifest.counters["cache_hits"] == 1


def test_record_failure_appends_and_increments_failed_counter(tmp_path: Path) -> None:
    cfg = Config()
    cfg.output._runs_root = tmp_path  # type: ignore[assignment]
    manifest = RunManifest(config=cfg)
    manifest.write_initial("issues --project 3060", {})
    manifest.record_failure("https://example.com", 500, "Server Error", "nid:12345")
    assert manifest.counters["failed"] == 1
    assert len(manifest["failures"]) == 1
    assert manifest["failures"][0]["status_code"] == 500


def test_mark_completed_sets_status(tmp_path: Path) -> None:
    cfg = Config()
    cfg.output._runs_root = tmp_path  # type: ignore[assignment]
    manifest = RunManifest(config=cfg)
    manifest.write_initial("issues --project 3060", {})
    manifest.mark_completed()
    assert manifest.status == "completed"


def test_mark_failed_sets_status_and_error(tmp_path: Path) -> None:
    cfg = Config()
    cfg.output._runs_root = tmp_path  # type: ignore[assignment]
    manifest = RunManifest(config=cfg)
    manifest.write_initial("issues --project 3060", {})
    manifest.mark_failed("Fatal error")
    assert manifest.status == "failed"


def test_load_raises_on_missing_file(tmp_path: Path) -> None:
    cfg = Config()
    cfg.output._runs_root = tmp_path  # type: ignore[assignment]
    with pytest.raises(FileNotFoundError):
        RunManifest.load("nonexistent", config=cfg)


def test_is_resumable_true_only_when_running(tmp_path: Path) -> None:
    cfg = Config()
    cfg.output._runs_root = tmp_path  # type: ignore[assignment]
    manifest = RunManifest(config=cfg)
    manifest.write_initial("issues --project 3060", {})
    assert manifest.is_resumable is True
    manifest.mark_completed()
    assert manifest.is_resumable is False


def test_record_source_mode(tmp_path: Path) -> None:
    cfg = Config()
    cfg.output._runs_root = tmp_path  # type: ignore[assignment]
    manifest = RunManifest(config=cfg)
    manifest.write_initial("issues --project 3060", {})
    manifest.record_source_mode("api")
    manifest.record_source_mode("html_fallback")
    manifest.record_source_mode("html_fallback")
    assert manifest["source_modes"]["api"] == 1
    assert manifest["source_modes"]["html_fallback"] == 2


def test_resume_from_existing_run(tmp_path: Path) -> None:
    cfg = Config()
    cfg.output._runs_root = tmp_path  # type: ignore[assignment]
    manifest = RunManifest(config=cfg)
    manifest.write_initial("issues --project 3060", {})
    manifest.update_cursor({"page": 3, "last_nid": 9999})
    reloaded = RunManifest.load(manifest.run_id, config=cfg)
    assert reloaded.cursor["page"] == 3
    assert reloaded.cursor["last_nid"] == 9999


def test_counters_default_to_zero(tmp_path: Path) -> None:
    cfg = Config()
    cfg.output._runs_root = tmp_path  # type: ignore[assignment]
    manifest = RunManifest(config=cfg)
    manifest.write_initial("issues --project 3060", {})
    assert manifest.counters["fetched"] == 0
    assert manifest.counters["succeeded"] == 0
    assert manifest.counters["failed"] == 0


def test_record_fallback_append(tmp_path: Path) -> None:
    cfg = Config()
    cfg.output._runs_root = tmp_path  # type: ignore[assignment]
    manifest = RunManifest(config=cfg)
    manifest.write_initial("changes --project 3060", {})
    manifest.record_fallback("https://drupal.org/project/drupal", "alias not found via API")
    assert len(manifest["_fallback_log"]) == 1
    assert manifest["_fallback_log"][0]["url"] == "https://drupal.org/project/drupal"
    assert manifest["_fallback_log"][0]["reason"] == "alias not found via API"

