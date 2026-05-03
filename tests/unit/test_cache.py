"""Unit tests for ResponseCache."""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import MagicMock

from drupal_crawl_ai.config import Config
from drupal_crawl_ai.http.cache import ResponseCache, _make_cache_key


def _isolated_cache(tmp_path: Path) -> ResponseCache:
    """Create a cache with an isolated directory."""
    cfg = Config()
    cfg.cache._cache_root = tmp_path  # type: ignore[assignment]
    cache = ResponseCache(cfg)
    # Override the backing field directly (bypassing the property)
    cache._cached_dir = tmp_path  # type: ignore[assignment]
    return cache


def test_make_cache_key_deterministic() -> None:
    key1 = _make_cache_key("GET", "https://example.com/api", {"b": 2, "a": 1})
    key2 = _make_cache_key("GET", "https://example.com/api", {"a": 1, "b": 2})
    assert key1 == key2


def test_make_cache_key_different_params_different_key() -> None:
    key1 = _make_cache_key("GET", "https://example.com/api", {"type": "project_issue"})
    key2 = _make_cache_key("GET", "https://example.com/api", {"type": "changenotice"})
    assert key1 != key2


def test_cache_miss_when_disabled(tmp_path: Path) -> None:
    cache = _isolated_cache(tmp_path)
    cache._enabled = False  # type: ignore[assignment]
    result = cache.get("GET", "https://example.com/api", {"type": "project_issue"})
    assert result is None


def test_cache_miss_missing_file(tmp_path: Path) -> None:
    cache = _isolated_cache(tmp_path)
    result = cache.get("GET", "https://example.com/api", {"type": "project_issue"})
    assert result is None


def test_cache_hit(tmp_path: Path) -> None:
    cache = _isolated_cache(tmp_path)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"nodes": []}'
    mock_response.json.return_value = {"nodes": []}

    cache.set("GET", "https://example.com/api", {"type": "project_issue"}, mock_response)

    result = cache.get("GET", "https://example.com/api", {"type": "project_issue"})
    assert result is not None
    assert result["status_code"] == 200


def test_cache_expired(tmp_path: Path) -> None:
    cache = _isolated_cache(tmp_path)
    cache._ttl_seconds = 0  # type: ignore[assignment]

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"nodes": []}'
    mock_response.json.return_value = {"nodes": []}

    cache.set("GET", "https://example.com/api", None, mock_response)

    entry_path = list(tmp_path.glob("*.json"))[0]
    with open(entry_path) as f:
        entry = json.load(f)
    entry["fetched_at"] = time.time() - 3600  # 1 hour ago
    with open(entry_path, "w") as f:
        json.dump(entry, f)

    result = cache.get("GET", "https://example.com/api", None)
    assert result is None
