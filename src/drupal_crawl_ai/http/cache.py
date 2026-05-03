"""Read-through HTTP response cache with TTL and deterministic key generation."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import requests

from drupal_crawl_ai.config import Config


def _make_cache_key(method: str, url: str, params: dict[str, Any] | None) -> str:
    """
    Build a deterministic cache key from method + url + sorted query params.

    Format: <method>|<path>|<sorted_param_hash>
    """
    if params:
        sorted_params = dict(sorted(params.items()))
        param_str = json.dumps(sorted_params, sort_keys=True, separators=(",", ":"))
    else:
        param_str = ""

    raw = f"{method}|{url}|{param_str}"
    return hashlib.sha1(raw.encode()).hexdigest()


class ResponseCache:
    """
    Read-through file-system cache for API HTTP responses.

    Stores responses as JSON files under ``cache_root/``, including metadata
    (status code, headers subset, fetched timestamp) alongside the raw body.
    """

    def __init__(self, config: Config | None = None) -> None:
        self._config = config or Config()
        self._cache_cfg = self._config.cache
        self._enabled = self._cache_cfg.enabled
        self._ttl_seconds = self._cache_cfg.ttl_hours * 3600
        self._cached_dir: Path | None = None

    @property
    def _cache_dir(self) -> Path:
        if self._cached_dir is None:
            self._cached_dir = self._cache_cfg.cache_dir()
        return self._cached_dir

    def _cache_path(self, key: str) -> Path:
        return self._cache_dir / f"{key}.json"

    def get(
        self, method: str, url: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """Return cached response dict if it exists and is not expired, else None."""
        if not self._enabled:
            return None

        key = _make_cache_key(method, url, params)
        path = self._cache_path(key)

        if not path.exists():
            return None

        try:
            with open(path, encoding="utf-8") as f:
                entry: dict[str, Any] = json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

        # TTL check
        fetched_at = entry.get("fetched_at", 0)
        if time.time() - fetched_at > self._ttl_seconds:
            return None

        return entry

    def set(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None,
        response: requests.Response,
    ) -> None:
        """Write a response into the cache."""
        if not self._enabled:
            return

        key = _make_cache_key(method, url, params)
        path = self._cache_path(key)

        body = response.text
        try:
            body = response.json()
        except Exception:
            pass  # store as raw text if not JSON

        entry = {
            "fetched_at": time.time(),
            "status_code": response.status_code,
            "url": url,
            "params": params,
            "body": body,
        }

        # Atomic write: temp file + rename
        tmp = path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(entry, f, indent=2, ensure_ascii=False)
        tmp.rename(path)
